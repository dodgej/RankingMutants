from game.Board import Board

m = 9
n = 4
k = 4
maxBoardStates = 3 ** (m * n)

for i in range(maxBoardStates):
    index = maxBoardStates - i - 1
    #index = i
    board, isUseful = Board.createBoardFromNumber(m, n, k, index)
    id = board.getBoardID()

    print("Index input : ", index, " and ID output: ", id, end="")
    print(board)
    if id != index:
        print("----------------------------------------------------\n----------------------------------------------------\n----------------------------------------------------\n----------------------------------------------------")
        print("violation!")