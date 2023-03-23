# Name:			cellSizeDataBase
# Summary:		Maps the cell array coordinates to their corresponding cell size. This is determined from our specific  
#               wafer architecture, which is unlikely to change.
#
# TODO: This is incomplete! Need to include verified sizes for all arrays in the grid.

DEFAULT = '10um'
cellSizes = {}

for row in range(5):  #from 0 to 4
    for col in range(16):  #from 0 to 15
        loc = f'({row},{col})'
        cellSizes[loc] = DEFAULT