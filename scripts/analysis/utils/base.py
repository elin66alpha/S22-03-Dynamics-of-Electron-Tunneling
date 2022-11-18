# Name:			base.py
# Summary:		Generates a report for EVERY CSV file.
# Refinement:   Rename to class name 
#
# Creator: 		Mihir Savadi

#import 
from resistanceAnalyzer.report import CellAnalyzerReport
from lib import *
from utils.csvItem import csvItem
from utils.cellSizeDataBase import cellSizes
from pdfGenerator.pdfgen import pdfGen

from tqdm import tqdm

# Name:			dataBaseCollator
# Summary:		Datatype for __.
# Desc:			This class employs the csvItem and pdfGen class to provide a single wrapper to deal with the entire database in one shot.
#
#               Does NOT call csvParser.
# Refinement:	Make this a datatype for a __, then have methods to __ SEPERATE from object init.
class dataBaseCollator :
    # Name:			__init__
    # Summary:		.
    # Desc:			.
    #
    #               Executes organizeCSVs() and generateSummaryReport().
    #
    # Refinement:	Make csvData NOT an instance variable, change to regular. Same with summaryDict.
    #               Remove all instance variables, make get functions.
    #
    # Input:		Path to the processed raw Keithley data CSVs, as a string.
    #               Path of where to store the generated reports, as a string.
    # Output:		None.
    def __init__(self, pathToData: str, pathToDump: str) :
        #store paths
        self.pathToData       = pathToData
        self.pathToDumpReport = pathToDump
        os.makedirs(self.pathToDumpReport)  #convert string to a path datatype

        # first convert all csv's in the data base into a dictionary of csvItem objects
        self.csvData = self.__organizeCSVs()
        
        self.summaryDict = self.__generateSummaryReport()

        # then create a pdf for each of these sublists using the pdfGenerator class and put them in a new reports
        # folder.
        for key,value in tqdm(self.csvData.items()) :
            pdfGen(value, self.summaryDict, self.pathToDumpReport)
            CellAnalyzerReport(value, self.summaryDict, self.pathToDumpReport).generateReport()

    # Name:			__organizeCSVs
    # Summary:		Organizes every CSV file in the given location.
    # Desc:			
    #               Creates a "csvItem" for every file.
    #               For every file with a unique cell coordinate (in the file name), add an entry to the result, with the cell coordinate
    #               as its key and the csvItem object representing the file as its value. For every "duplicate" file with the same cell coordinate, 
    #               add its csvItem object to the value of that entry.
    #               Finally, sort the value of each entry (file objects) by time stamp.
    #               
    #               Contains nested method definition.
    #
    # Refinement:	Make self.pathToData NOT a instance var, make it an input argument
    #
    # Input:		Path for CSVs, as a string.
    # Output:		Organized files, as an ordered dictionary.
    def __organizeCSVs(self) -> OrderedDict :
        csvFileNames = os.listdir(self.pathToData)

        # first fill up entire dictionary
        cellDataDict = OrderedDict()
        for csv in csvFileNames :  #for every file
            csvItemObject = csvItem(self.pathToData + csv)

            # if target cell doesn't exist in dict create empty list then append to it, otherwise just append.
            if cellDataDict.get(f'{csvItemObject.targetCellCoord}') == None :
                cellDataDict[f'{csvItemObject.targetCellCoord}'] = []

            cellDataDict[f'{csvItemObject.targetCellCoord}'].append(csvItemObject)  #add csvItem object to result

            # do same as above but for neighbor cell
            if csvItemObject.neighborCellCoord[0] != '<' :  #when neighbor cell exists
                #update result
                if cellDataDict.get(f'{csvItemObject.neighborCellCoord}') == None :
                    cellDataDict[f'{csvItemObject.neighborCellCoord}'] = []
                cellDataDict[f'{csvItemObject.neighborCellCoord}'].append(csvItemObject)  #add csvItem object to result

        # then time order each entry in the dictionary
        def sortingKey(csvItemObj: csvItem) -> int :
            return csvItemObj.timeStamp_whole

        for key, value in cellDataDict.items() :
            value.sort(key=sortingKey)

        #done
        return cellDataDict
        
    # Name:			__generateSummaryReport
    # Summary:		Generates a cells used summary report.
    # Desc:			Includes information about the cells accessed, their size, when it was last accessed, and number of times stimulated.
    #
    #               All summary report information stored as a text file and an ordered dictionary.
    #               
    # Refinement:	.
    #
    # Input:		CSV cell data, as an ordered dictionary.
    # Output:		The summary report, as an ordered dictionary.     
    def __generateSummaryReport(self) -> dict:
        #init
        summaryReportDict = OrderedDict()  #result
        
        #
        for key, value in self.csvData.items() :  #for every entry, not every csv file in path 
            cellSummaryDict = OrderedDict()

            firstCSV = value[0]

            cell_t_split = firstCSV.targetCellCoord.split(',')
            arrayCoordinates = f'({cell_t_split[1]},{cell_t_split[2]})'

            cellSummaryDict["cellSize"] = cellSizes[arrayCoordinates]

            cellSummaryDict['timesAccessed'] = len(value)

            cellSummaryDict['lastAccessed'] = f'{value[-1].timeStamp_year}/{value[-1].timeStamp_month}/{value[-1].timeStamp_day} at {value[-1].timeStamp_time12hr}'

            summaryReportDict[key] = cellSummaryDict

        outputTextFile = ["Cell Coordinate,Cell Size,no. of times stimulated,last stimulated"]
        for key, value in summaryReportDict.items() :
            outputTextFile.append(f"({key}),{value['cellSize']},{value['timesAccessed']},{value['lastAccessed']}")

        file = open(self.pathToDumpReport+f'/cellsUsedSummary.txt', 'w')
        for line in outputTextFile :
            file.write(line+'\n')
        file.close()
        
        #done
        return summaryReportDict