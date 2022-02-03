import torch
import torch.nn as nn


torch.random.manual_seed(31)

softmaxFn = nn.Softmax(dim=0)
gumbelSoftmaxFn = nn.functional.gumbel_softmax
test1 = torch.rand(3)

print("test1: ", test1)
print("result: ", softmaxFn(test1))
print()

test2 = torch.zeros(3)
test2[0] = 8
test2[1] = 5

print("test2: ", test2)
print("result: ", softmaxFn(test2))
print()

test3 = torch.rand(36)

print("test3: ", test3)
print("result: ", softmaxFn(test3))
print()

test4 = torch.zeros(36) - 1
test4[0] = 1
test4[1] = .5

print("test4: ", test4)
print("result: ", softmaxFn(test4))
print()

test5 = torch.zeros(36) - 1
test5[0] = 1
test5[1] = .5
test5 *= 100

print("test5: ", test5)
print("result: ", softmaxFn(test5))
print()

test6 = torch.rand(36)
test6 *= 100

print("test6: ", test6)
print("result: ", softmaxFn(test6))
print()

temperature = 1
print("Gumbel t=", temperature, gumbelSoftmaxFn(test6, temperature))
print()

temperature = 20
print("Gumbel t=", temperature, gumbelSoftmaxFn(test6, temperature))
print()

temperature = .1
print("Gumbel t=", temperature, gumbelSoftmaxFn(test6, temperature))
print()


test7 = torch.Tensor([ -24.1949,  -41.0825,  -22.7823,   -2.2092,  -83.5751,  -81.0165,
         -86.8102,    9.3951,  -42.6996,  -36.5448,  -25.0036,  -92.1702,
         -93.3001, -100.0000, -100.0000, -100.0000,   -7.0868,  -84.7552,
          -9.6358,  -83.7496,  -27.3628,  -94.0693,  -92.6596, -100.0000,
         -89.1023,  -96.8599,  -15.1874,  -20.0030,  -35.6189,   -7.2431,
         -16.9730,  -49.8817,  -78.5738,  -28.9532,   -2.7728,  -38.6922])

print("Gumbel t=", temperature, gumbelSoftmaxFn(test7, temperature))
print()