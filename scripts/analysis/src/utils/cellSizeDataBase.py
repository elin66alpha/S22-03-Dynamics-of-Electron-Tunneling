# Name:			.
# Summary:		.

# this is a dictionary mapping the array coordinates (not a complete coordinate) to the cell size. This is
# predetermined from the wafer architecture we've been using, which is unlikely to change at any point in the near
# future.
# TODO: This is incomplete! Need to include sizes for all the arrays in the grid
# TODO: Code assumes below sizes REGARDLESS of array location. Fix this.

cellSizes = {
    '(0,0)' : '10um',
    '(0,1)' : '10um',
    '(0,2)' : '10um',
    '(0,4)' : '10um',    
    '(0,6)' : '10um',
    '(0,7)' : '10um',
    '(1,5)' : '10um',
    '(0,13)' : '10um',

    '(1,0)' : '10um',
    '(1,1)' : '10um',
    '(1,2)' : '10um',
    '(2,2)' : '10um',
    '(2,3)' : '10um',
    '(3,0)' : '10um',  #verify
    '(3,3)' : '10um',  #verify

}

#array (0,0)
# cellSizes = {

#array (6,6)  #what is max?
# cellSizes = {
