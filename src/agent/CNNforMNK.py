import torch
import torch.nn as nn
import torch.nn.functional as F

from torch.autograd import Variable
from torch.distributions import Normal
from settings import settings

# The goal of this CNN is to encode a function that maps a Board -> Outcome Tensor, where the outcome tensor associates
# a (Win%, Draw%, Loss%) tuple to each square on the board. This creates a 3D brick of numbers, of shape (M, N, 3)
class CNNforMNK(torch.nn.Module):
    def __init__(self, m, n, numOutcomes):
        torch.nn.Module.__init__(self)
        boardSize = m*n
        input_channels = 2 # my pieces, your pieces
        kernelSize = 3 # size of CNN filters (same all layers)
        conv3_stride = 2
        strideM = int(float(m)/float(conv3_stride) + 0.5)
        strideN = int(float(n)/float(conv3_stride) + 0.5)
        self.strideBoardSize = strideN * strideM
        conv1_outputs = 131 # size of hidden space based on summary statistics of the board
        conv2_outputs = 87 # size of second hidden space based on summary statistics of the first hidden space
        conv3_outputs = 61
        conv4_outputs = 53
        self.conv5_outputs = 37

        self.conv1 = nn.Conv2d(input_channels,  conv1_outputs, kernelSize, padding=int(kernelSize / 2))
        self.conv2 = nn.Conv2d(conv1_outputs,   conv2_outputs, kernelSize, padding=int(kernelSize / 2))
        self.conv3 = nn.Conv2d(conv2_outputs,   conv3_outputs, kernelSize, padding=int(kernelSize / 2), stride=conv3_stride)
        self.conv4 = nn.Conv2d(conv3_outputs,   conv4_outputs, kernelSize, padding=int(kernelSize / 2))
        self.conv5 = nn.Conv2d(conv4_outputs,   self.conv5_outputs, kernelSize, padding=int(kernelSize / 2))
        self.fc1 = nn.Linear(self.conv5_outputs * self.strideBoardSize, boardSize)
        self.outcomes = nn.Linear(boardSize, boardSize * numOutcomes)

    def forward(self, x):
        if torch.cuda.is_available():
            x = x.cuda()

        x = F.relu(self.conv1(x))
        x = F.relu(self.conv2(x))
        x = F.relu(self.conv3(x))
        x = F.relu(self.conv4(x))
        x = F.relu(self.conv5(x))
        x = x.view(-1, self.conv5_outputs * self.strideBoardSize)
        x = F.relu(self.fc1(x))
        x = self.outcomes(x)
        output = torch.sigmoid(x)

        return output

    # helper that calls the forward pass, but neatly wraps the CPU/GPU storage of the proper data
    def evaluateBoard(self, board, typeInThisGame):
        boardTensor = board.exportToNN(typeInThisGame)

        # do the forward pass
        if torch.cuda.is_available():
            nnOutput = self.forward(Variable(boardTensor.cuda()))
        else:
            nnOutput = self.forward(Variable(boardTensor))

        return nnOutput

    # does the backward pass with our loss function and updates the learned weights
    def weightUpdate(self, nnOutput, target, optimizer):
        # FIXME consider working with Dr. Dietterich on this part, but I cannot figure out how to build the dirichlet into this
        # PPO (proximal policy updates) off the shelf, last resort. might not be appropriate if I am trying to get probabilities
        loss = CNNforMNK.lossFunction(nnOutput, Variable(target))
        optimizer.zero_grad()
        loss.backward()
        norm = torch.nn.utils.clip_grad_norm_(self.parameters(), 1)
        optimizer.step()

        return loss

    @staticmethod
    def lossFunction(nnOutput, target):
        loss = nn.L1Loss(reduction='sum')(nnOutput, Variable(target))
        #loss = nn.KLDivLoss(reduction='sum')(nnOutput.log(), Variable(target))
        #FIXME decide on some weights we like, scaling on the right parts of the tensor

        # FIXME grab the first column, call it a winning moves mask
        # where is probability above some threshold (use a boolean false tensor, set things to true that you want, then myArr[mask]
        # stretch by board size, add 1
        # loss = nn.L1Loss(reduction='none')(nnOutput, Variable(target))
        # totalLossRaw = loss.sum()
        #
        #
        # weights = torch.ones(loss.shape) * 5.0
        # print("NN OUTPUT: ", nnOutput.reshape((settings.numOutcomes, settings.n, settings.m)).transpose(0, 2))
        # print("TARGET: ", target.reshape((settings.numOutcomes, settings.n, settings.m)).transpose(0, 2))
        # print("SUM: ", totalLossRaw)
        # print("LOSS: ", loss)
        # print("WEIGHTS: ", weights)
        #
        # loss = torch.dot(loss[0], weights[0])
        return loss

    # blast the specified layer with noise, by adding a Gaussian with specified mean/sd
    @staticmethod
    def noisifyLayer(layer, mean, sd):
        shape = layer.weight.shape
        with torch.no_grad():
            noiseTensor = Normal(mean, sd).sample(shape)
            layer.weight += noiseTensor
