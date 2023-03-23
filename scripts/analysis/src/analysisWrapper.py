# Name:			analysisWrapper.py
# Summary:		Contains functions to analyze data. NOT datatype classes.
#
# Refinement:   Potentially move generate reports private methods to generateReport.py or a new file.

#import dependencies  
import os
import matplotlib.pyplot as plt
import shutil
from collections import OrderedDict
from tqdm import tqdm

from src.utils.CsvFile import CsvFile
from src.utils.cellSizeDataBase import cellSizes
import src.generateReport as generateReport

#pdfGen
from matplotlib.pyplot import savefig

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import utils

#PUBLIC 

# Name:			convert_csv_files
# Summary:		Convert csv files' data to a datatype. / Create csv files datatype.
# Desc:			.
# Refinement:	.
#
# Input:		Path to the processed raw Keithley data CSVs, as a string.
# Output:		The data, csvData, as an ordered dictionary.
def convert_csv_files(path):
    return __organizeCSVs(path)  #data for all csv files in path

# Name:			generate_reports
# Summary:		.
# Desc:			Generates a report for EVERY CSV file.
# Refinement:	.
#
# Input:		The output path to store the generated reports, as a string. 
#               The data, csvData, as an ordered dictionary.
# Output:		None.
def generate_reports(path, csvData):
    #init
    p = path  #copy path
    os.makedirs(p)  #convert to a path datatype

    #create cells used text file and variable
    summaryDict = __generateSummaryReport(p, csvData)

    # then create a pdf for each of these sublists using the pdfGenerator class and put them in a new reports
    # folder.
    for key,value in tqdm(csvData.items()) :  #grab the value, all csvItems for a cell, of each csvData entry
        __pdfGen(value, summaryDict, path)  #combine
        generateReport.generateReport(value, summaryDict, path)
#end generate_reports()  
  
  
  
#PRIVATE (have not tested to see if using "__name" actually makes it "private" from main script)

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
# Refinement:	.
#
# Input:		Path for CSVs, as a string.
# Output:		Organized files, as an ordered dictionary, csvData.
def __organizeCSVs(inputDataPath) -> OrderedDict :
    # find all csv files, filter out README.md
    csvFileNames = os.listdir(inputDataPath)
    if "README.md" in csvFileNames:
        csvFileNames.remove("README.md")

    # first fill up entire dictionary
    cellDataDict = OrderedDict()
    for csv in csvFileNames :  #for every file
        csvItemObject = CsvFile(inputDataPath + csv)

        # if target cell doesn't exist in dict create empty list then append to it, otherwise just append.
        if cellDataDict.get(f'{csvItemObject.heatedCellCoord}') == None :
            cellDataDict[f'{csvItemObject.heatedCellCoord}'] = []

        cellDataDict[f'{csvItemObject.heatedCellCoord}'].append(csvItemObject)  #add csvItem object to result

        # do same as above but for neighbor cell
        if csvItemObject.observedCellCoord[0] != '<' :  #when neighbor cell exists
            #update result
            if cellDataDict.get(f'{csvItemObject.observedCellCoord}') == None :
                cellDataDict[f'{csvItemObject.observedCellCoord}'] = []
            cellDataDict[f'{csvItemObject.observedCellCoord}'].append(csvItemObject)  #add csvItem object to result

    # then time order each entry in the dictionary
    def sortingKey(csvItemObj: CsvFile) -> int :
        return csvItemObj.timeStamp_whole

    for key, value in cellDataDict.items() :
        value.sort(key=sortingKey)

    #done
    return cellDataDict
#end __organizeCSVs()
  
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
def __generateSummaryReport(output_path, csvData) -> dict:
    #init
    summaryReportDict = OrderedDict()  #result
    
    #
    for key, value in csvData.items() :  #for every entry, not every csv file in path 
        cellSummaryDict = OrderedDict()

        firstCSV = value[0]

        cell_t_split = firstCSV.heatedCellCoord.split(',')
        arrayCoordinates = f'({cell_t_split[1]},{cell_t_split[2]})'

        cellSummaryDict["cellSize"] = cellSizes[arrayCoordinates]

        cellSummaryDict['timesAccessed'] = len(value)

        cellSummaryDict['lastAccessed'] = f'{value[-1].timeStamp_year}/{value[-1].timeStamp_month}/{value[-1].timeStamp_day} at {value[-1].timeStamp_time12hr}'

        summaryReportDict[key] = cellSummaryDict

    outputTextFile = ["Cell Coordinate,Cell Size,no. of times stimulated,last stimulated"]
    for key, value in summaryReportDict.items() :
        outputTextFile.append(f"({key}),{value['cellSize']},{value['timesAccessed']},{value['lastAccessed']}")

    file = open(output_path+f'/cellsUsedSummary.txt', 'w')
    for line in outputTextFile :
        file.write(line+'\n')
    file.close()
    
    #done
    return summaryReportDict
#end __generateSummaryReport()


#BEGIN pdfgen.py
# Name:			__pdfgen
# Summary:		.
# Desc:			Generates a PDF file with csv data.
# Refinement:	.
#
# Input:		csvItemObjList : typing.List 
#                   (Note that this list needs to be time ordered and only have cells of one coordinate -- this is all handled by the dataBaseCollator class.)
#               summaryDict : ordered dictionary
#                   Contains summary information about the cell in question.
#               pdfDumpPath : str
#                   Path to output the pdf, as a string.
# Output:		None.
def __pdfGen(csvItemObjList: list([CsvFile]), summaryDict: dict, pdfDumpPath: str) -> None:
    cellCoord = csvItemObjList[0].heatedCellCoord
    cellSummaryDict = summaryDict[cellCoord]
    
    # setup document
    doc = SimpleDocTemplate(
        pdfDumpPath + f"/({cellCoord})_plots.pdf",
        pagesize=letter,
        rightMargin=35, leftMargin=35,
        topmargin=10, bottommargin=18,
    )
    styles = getSampleStyleSheet()

    flowables = [] # this is the series of items to be produced in our pdf

    # add heading
    flowables.append(Paragraph('('+cellCoord+') Plots and Summary', styles["Heading1"]))

    # add summary details
    flowables.append(Paragraph(f"- Cell Size = {cellSummaryDict['cellSize']}", styles["BodyText"]))
    flowables.append(Paragraph(f"- Number of Times Accessed = {cellSummaryDict['timesAccessed']}", 
        styles["BodyText"]))
    flowables.append(Paragraph(f"- Last Stimulated = {cellSummaryDict['lastAccessed']}", styles["BodyText"]))
    flowables.append(Paragraph(f"-------------------------------------------------", styles["BodyText"]))

    # add sections with plots for each csv
    tempImageDir = pdfDumpPath+f'tempImgs/'
    os.makedirs(tempImageDir)
    for i, csvObj in enumerate(csvItemObjList) :
        plots = csvObj.getPlots()

        flowables.append(Paragraph(f"Stimulated at {csvObj.timeStamp_time12hr} on {csvObj.timeStamp_year}/{csvObj.timeStamp_month}/{csvObj.timeStamp_day} ", 
            styles["BodyText"]))
        flowables.append(Paragraph(f"Activity = {csvObj.activity}", 
            styles["BodyText"]))
        flowables.append(Paragraph(f"Start Voltage = {csvObj.startVoltage}", 
            styles["BodyText"]))
        flowables.append(Paragraph(f"End Voltage = {csvObj.endVoltage}", 
            styles["BodyText"]))
        flowables.append(Paragraph(f"Ramp Rate = {csvObj.rampRate}", 
            styles["BodyText"]))
        flowables.append(Paragraph(f"Compliance Current = {csvObj.complianceCurrent}{csvObj.complianceCurrentUnits}", 
            styles["BodyText"]))
        flowables.append(Paragraph(f"Platinum Voltage = {csvObj.platinumVoltage}", 
            styles["BodyText"]))
        flowables.append(Paragraph(f"Copper Voltage = {csvObj.copperVoltage}", 
            styles["BodyText"]))
        flowables.append(Paragraph(f"Run Folder Name = {csvObj.runFolderName}", 
            styles["BodyText"]))
        flowables.append(Paragraph(f"Comments = {csvObj.comments}", 
            styles["BodyText"]))

        if type(plots['probe A plot']) != str :
            imgDir = tempImageDir+f'{i}_tempFigA.jpg'
            plots['probe A plot'].savefig(imgDir,bbox_inches='tight',dpi=100)
            flowables.append(__getImage(imgDir, 400))
            plt.close(plots['probe A plot']) # do this to save memory

        if type(plots['probe B plot']) != str :
            imgDir = tempImageDir+f'{i}_tempFigB.jpg'
            plots['probe B plot'].savefig(imgDir,bbox_inches='tight',dpi=100)
            flowables.append(__getImage(imgDir, 400))
            plt.close(plots['probe B plot']) # do this to save memory

        if type(plots['probe C plot']) != str :
            imgDir = tempImageDir+f'{i}_tempFigC.jpg'
            plots['probe C plot'].savefig(imgDir,bbox_inches='tight',dpi=100)
            flowables.append(__getImage(imgDir, 400))
            plt.close(plots['probe C plot']) # do this to save memory

        flowables.append(Paragraph(f"-------------------------------------------------", 
            styles["BodyText"]))

    doc.build(flowables)

    shutil.rmtree(tempImageDir)
#end __pdfGen()

# Name:			__getImage
# Summary:		.
# Desc:			Makes resizing images to scale easy.
# Refinement:	.
#
# Input:		.
# Output:		.  
def __getImage(path, width=1):
    img = utils.ImageReader(path)
    iw, ih = img.getSize()
    aspect = ih / float(iw)
    return Image(path, width=width, height=(width * aspect))
#end __getImage()
#END pdfgen.py