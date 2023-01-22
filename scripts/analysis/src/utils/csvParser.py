# Name:			.
# Summary:		Datatype containing methods to parse a CSV file.
# Desc:         This file contains functions to extract comments, title row, and columns from each csv, according to the format
#               established in the project summary document.

#import dependencies  
import typing

#PUBLIC

#
# Name:			parseCsv
# Summary:		Creates a CSV file object.
# Desc:			Extracts the file's comments, column titles, and column data. 
#               
#               Creates list of lines represented as strings. Each entry is one file line. This is used to populate these
#               instance variables. The comments, titles, and data respectively are extracted from the file.
# Refinement:	.
#
# Input:		The CSV file path, as a string.
# Output:		A tuple.
def parseCsv(csvPath: str):
    #parse file into lines 
    file = open(csvPath, 'r', encoding = 'utf8')  #open the file 
                                                  #to run on windows, OG was open(csvPath, 'r')
    lines = [line for line in file]
    lastCommentLineIdx = -1 # this is modified by self.__extractTitle() if comments are included
    file.close()  #close the file
    
    #extract and store file 
    # need to be excecuted in this order here, since methods have order dependency
    comments, lines, lastCommentLineIdx = __extractComments(lines, lastCommentLineIdx)
    title, lines, lastCommentLineIdx = __extractColumnTitles(lines, lastCommentLineIdx)
    columns  = __extractColumnData(lines, lastCommentLineIdx, title)

    return title, comments, columns 

#PRIVATE

# Name:			__extractComments
# Summary:		Search file for comments.
# Desc:			Uses file lines instance variable to search for any comments.
#               Assumes comments only exist, were appended, before the measurement data, and the lines immediately before and after 
#               the comments are exactly "---".
#               Checks if the first line of the file must be "---". If not, it is assumed no comments exist.
# Refinement:	.
#
# Input:		None.
# Output:		The comments, as a string. When no comments, result is "No comments were added.", as opposed to an empty string.
def __extractComments(lines, lastCommentLineIdx) -> str :
    comments = ''  #result

    #check first line of file
    if lines[0].replace(" ", "") == '---\n' :  #when comments exist
        commentsStarted = False
        for i, line in enumerate(lines) :  #extract lines until see "---" indicator
            if line.replace(" ", "") == '---\n' and commentsStarted == False :
                commentsStarted = True
                continue
            if commentsStarted == True :
                if line.replace(" ", "") == '---\n' :
                    lastCommentLineIdx = i
                    break
                else:
                    comments += line  #append line to result

        if comments[-1] == '\n':
            comments = comments[:-1]

    else :  #when comments do not exist
        comments = "No comments were added."

    #done
    return comments, lines, lastCommentLineIdx

# Name:			__extractColumnTitles
# Summary:		Search file for column titles.
# Desc:			.
# Refinement:	.
#
# Input:		None.
# Output:		The titles, as a list of strings. Each entry is the title of the respective column of the csv.
def __extractColumnTitles(lines, lastCommentLineIdx) -> typing.List[str] :    
    title = lines[lastCommentLineIdx+1][:-1].split(',')
    return title, lines, lastCommentLineIdx

# Name:			__extractColumnData
# Summary:		Searches file for column data.
# Desc:			Splits lines of data.
#
#               Assumes extracted comments from file first, as the column data starts after the comments.
# Refinement:	Add error checking for if comments have been sucessfully extracted yet.
#
# Input:		None.
# Output:		The columns of data (List[List[float]]), as a list of lists, where each entry in each secondary list is 
#               a float. Each secondary list represents the respective column of the CSV
def __extractColumnData(lines, lastCommentLineIdx, title) -> typing.List[typing.List[float]] :
    columns = []  #result
    
    #search
    firstLine = lines[lastCommentLineIdx+2][:-1].split(',')  #split first line that is not a comment
    for i in range(0, len(title)) :
        columns.append([float(firstLine[i])])

    for line in lines[lastCommentLineIdx+3:] :
        # skip blank lines
        if len(line.strip()) == 0:
            continue

        splitLine = line[:-1].split(',')
        for j in range(0, len(title)) :
            columns[j].append(float(splitLine[j]))

    #done
    return columns