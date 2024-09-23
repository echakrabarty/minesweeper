from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options

import time
import numpy as np

driver = webdriver.Chrome()

actionChains = ActionChains(driver)

driver.get("https://minesweeperonline.com/#intermediate")

start = driver.find_element(By.ID, "1_1")
start.click()

def scanBoard(type):
    if type == "B":
        dim = (9,9)
    if type == "I":
        dim = (16,16)
    if type == "E":
        dim = (16,30)
    values = []
    squares = driver.find_elements(By.XPATH, "//div[starts-with(@class,'square')]")
    for i in range(dim[0]*dim[1]):
        className = squares[i].get_attribute("class")
        squareType = className.split()[1]
        if squareType[0] == "o":
            values.append(squareType[-1])
        elif squareType == "bombflagged":
            values.append("F")
        else:
            values.append(" ")
    board = np.reshape(values, dim)
    return board

def getNeighbors(board, x, y):
    res = {}
    dim_x, dim_y = np.shape(board)
    dim_x -= 1
    dim_y -= 1
    neighbors = []
    coord = []
    #make sure its not in first row
    if y != 0:
        neighbors.append(board[x][y-1])
        coord.append((x,y-1))
    #make sure its not in right extreme
    if x != dim_x:
        neighbors.append(board[x+1][y])
        coord.append((x+1,y))
    # check left extreme
    if x != 0:
        neighbors.append(board[x-1][y])
        coord.append((x-1,y))
    # make sure its not on last row
    if y != dim_y:
        neighbors.append(board[x][y+1])
        coord.append((x,y+1))
    #check upper right corner
    if x != dim_x and y != 0:
        neighbors.append(board[x+1][y-1])
        coord.append((x+1,y-1))
    #check bottom left
    if x != 0 and y != dim_y:
        neighbors.append(board[x-1][y+1])
        coord.append((x-1,y+1))
    # chek bottom right
    if x != dim_x and y != dim_y:
        neighbors.append(board[x+1][y+1])
        coord.append((x+1,y+1))
    # check top left
    if x != 0 and y != 0:
        neighbors.append(board[x-1][y-1])
        coord.append((x-1,y-1))
    res = dict(zip(coord,neighbors))
    return res

def flag(coords):
    x = coords[0]
    y = coords[1]
    coord = str(x+1) + "_" + str(y+1)
    print("flagging" + coord)
    square = driver.find_element(By.ID, coord)
    actionChains.context_click(square).perform()

def mine(coords):
    x = coords[0]
    y = coords[1]
    coord = str(x+1) + "_" + str(y+1)
    print("demining " + coord)
    square = driver.find_element(By.ID, coord)
    square.click()

def scanPotential(board):
    potential = {}
    height, width = np.shape(board)
    for i in range(height):
        for j in range(width):
            if not board[i][j].isnumeric():
                continue
            neighbor_dict = getNeighbors(board, i, j)
            neighbor_vals = list(neighbor_dict.values())
            n_coords = list(neighbor_dict.keys())
            nFlags = neighbor_vals.count("F")
            if neighbor_vals.count(" ") == 0:
                continue
            c_pot = []
            for k in n_coords:
                if neighbor_dict[k] == " ":
                    c_pot.append(k)
            potential[(i,j)] = [c_pot,int(board[i,j])-nFlags]
            # potential = {}
            # key = target coord
            # value = [blank neighbor coords, remaining flags (# of flags in these coords)]
    return potential

                

def basicStrategy(board, type):
    print("Using Basic Strategy")
    height, width = np.shape(board)
    for i in range(height):
        for j in range(width):
            if board[i][j] == "0" or board[i][j] == " ":
                continue
            neighbor_dict = getNeighbors(board, i, j)
            neighbors = list(neighbor_dict.values())
            nBlank = neighbors.count(" ")
            if nBlank == 0:
                continue
            coords = list(neighbor_dict.keys())
            nFlag = neighbors.count("F")
            
            # if square = n and n neighbors are flags, mine all neighbors
            if board[i][j].isnumeric and str(nFlag) == board[i][j]:
                for i in range(len(neighbors)):
                    if neighbors[i] == " ":
                        mine(coords[i])
                return scanBoard(type)
            # if square = n and n neighbors are blank, flag all neighbors
            elif board[i][j].isnumeric() and str(nBlank+nFlag) == board[i][j]:
                for i in range(len(neighbors)):
                    if neighbors[i] == " ":
                        flag(coords[i])
                return scanBoard(type)
    return scanBoard(type)


def groupStrat(board, type):
    print("Using group strategy")
    potential = scanPotential(board)
    height, width = np.shape(board)
    for i in range(height):
        for j in range(width):
           if (i,j) not in list(potential.keys()):
                continue
           neighbor_dict = getNeighbors(board, i, j)
           n_coords = list(neighbor_dict.keys())
           for k in n_coords:
                if k not in list(potential.keys()):
                    continue 
                nFlags = potential[k][1]
                # len(potential[(i,j)][0] - potential[k][0])  = # of target neighbors not within neighbor group 
                # nFlags is neighbor group number
                # get target number flags remaining 
                remainingFlags = potential[(i,j)][1]
                # check if a neighbor group is within the target's neighbors
                targetNeighborGroup = set(potential[(i,j)][0])
                neighborGroup = set(potential[k][0])
                if targetNeighborGroup - neighborGroup == targetNeighborGroup ^ neighborGroup and len(targetNeighborGroup-neighborGroup)>0:
                    # how many flags are in the neighboring group? nFlags
                    # how many flags does the target still need? remainingFlags
                    # if equal then remaining mines are flags
                    bombs = remainingFlags - nFlags
                    if bombs == 0:
                        for minable in list(targetNeighborGroup - neighborGroup):
                            mine(minable)
                        return scanBoard(type)
                    elif bombs == len(targetNeighborGroup - neighborGroup):
                        for flaggable in list(targetNeighborGroup - neighborGroup):
                            flag(flaggable)
                        return scanBoard(type)
    return scanBoard()

type = "I"
board = scanBoard(type)
print(board)

new = board
try:
    while " " in set(board.flatten()):
        new = basicStrategy(board, type)
        if np.array_equal(new, board):
            new = groupStrat(board, type)
            if np.array_equal(new,board):
                board = new
                break
        board = new
except:
    print("e: " + str(IOError))
board = new
print(board)

if " " in set(board.flatten()):
    print("L")
else: 
    print("W")

time.sleep(60)
driver.quit()


# data: solved board, correct board

