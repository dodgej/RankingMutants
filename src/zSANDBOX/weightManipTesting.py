import torch
from torch.distributions import Normal
from agent.CnnAgent import CnnForMNK


def noisifyLayer(layer, mean, sd):
    shape = layer.weight.shape
    with torch.no_grad():
        noiseTensor = Normal(mean, sd).sample(shape)
        layer.weight += noiseTensor

def zeroLayer(layer):
    with torch.no_grad():
        shape = layer.weight.shape
        for i in range(shape[0]):
            for j in range(shape[1]):
                layer.weight[i, j] = 0

nn = CnnForMNK(9,4,3)
mean = 0
sd = 1

zeroLayer(nn.fc1)
print(nn.fc1.weight)
noisifyLayer(nn.fc1, mean, sd)
print(nn.fc1.weight)
zeroLayer(nn.fc1)
print(nn.fc1.weight)
noisifyLayer(nn.fc1, mean, 10*sd)
print(nn.fc1.weight)



