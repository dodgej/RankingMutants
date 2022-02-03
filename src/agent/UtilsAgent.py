import random

class ScalarField:
    def __init__(self, m, n):
        self.data = [[0 for rows in range(n)] for cols in range(m)]  # scalar field representing the final composite score

    def __init__(self, torchMatrix):
        self.data = torchMatrix.transpose(0,1).tolist()

    def getScalar(self, i, j):
        return self.data[i][j]
