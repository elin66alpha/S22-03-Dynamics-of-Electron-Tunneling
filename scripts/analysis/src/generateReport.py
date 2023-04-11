# Name:			generateReport.py
# Desc:			Takes in CSV files, analyzes the properties of the cells using the CellAnalyzer, and creates a special pdf report containing that information.
#   
# Limitations:  Currently only supports 2-probe measurements.
# Refinement:	Move ProcessState to a new file, since it is copied in more than one place in repo.

#import dependencies  
import os
import shutil
from dataclasses import dataclass
import pandas
from typing import Iterable, Dict, List, OrderedDict
import math
import matplotlib.pyplot as plt
import seaborn as sns

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image, PageBreakIfNotEmpty, Table, ListFlowable, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import utils

import src.CellAnalyzer as ca
from src.utils.CsvFile import CsvFile

defaultFontSize = 15
titlePlotFontSize = 22
axisLabelFontSize = 18
LINE_WIDTH = 3  #pixel thickness

#for poster image generation        
#DEFAULT_DPI = 800  
#PLOT_WIDTH = 600 
#memory saver
DEFAULT_DPI = 300  
PLOT_WIDTH = 400
            
# Name:			generateReport
# Summary:		Generates a PDF file and outputs a pdf in the folder path.
#
# Input:		csvItems : List[csvItem] 
#                   Chronological list of CSV files all belonging to a single cell
#               summaryDict : Dict[str, object]
#                   Cell usage summary dict created by databaseCollator
#               pdfFolder : str
#                   Folder in which to save PDF file
# Output:		None.
def generateReport(csvItems: List[CsvFile], summaryDict: Dict[str, object], pdfFolder: str):
    #init
    cellCoord = csvItems[0].heatedCellCoord
    pdfFolder = pdfFolder
    pdf_name = f"{pdfFolder}/({cellCoord})_characteristics.pdf"

    items = csvItems

    cellSummaryDict = summaryDict[cellCoord]
    cellSize = cellSummaryDict['cellSize']
    timesAccessed = cellSummaryDict['timesAccessed']
    lastAccessed = cellSummaryDict['lastAccessed']
    global df
    df = pandas.DataFrame(columns=['Cycle', 'Set Icc', 'Set Voltage', 'R_on', 'R2', 'Set Data', 'Reset Data'], copy=True)
    summaryTable = [["Cycle #", "Set Icc (μA)", "Set Voltage (V)", "R_on (Ω)", "R2"]]
    #summaryTable.append([None, None, None, None, None])
    
    #generate report 
    
    tmpDir = f'{pdfFolder}/({cellCoord})-dump'
    os.makedirs(tmpDir)

    # setup document
    doc = SimpleDocTemplate(
        pdf_name,
        pagesize=letter,
        rightMargin=35, leftMargin=35,
        topmargin=10, bottommargin=18,
    )

    styles = getSampleStyleSheet()

    # this is the series of items to be produced in our pdf
    flowables = [    
        # add heading
        Paragraph(f'({cellCoord}) Characteristics', styles["Heading1"]),
        Paragraph(f'——————————————————————————————————', styles["Heading2"]),
        ListFlowable(
            [
                Paragraph(f"<b>Cell Size:</b> {cellSize}", styles["BodyText"]),
                Paragraph(f"<b>Times Accessed:</b> {timesAccessed}", styles["BodyText"]),
                Paragraph(f"<b>Last Measurement:</b> {lastAccessed}", styles["BodyText"])
            ],
            bulletType='bullet'
        ),
        Paragraph("Summary", styles["Heading4"])
    ]

    pages = []
    

    for i, page in enumerate(items):  #items is a list of all CSV files belonging to a single cell
        
        
        if page.activity == 'observe':
            continue

        for flowable in __generatePage(page, i, tmpDir, df, summaryTable):  #df and summaryTable modified by method
            pages.append(flowable)
        
        # put each operation on its own page
        #if i < len(items) - 1:
            #pages.append(PageBreakIfNotEmpty())
    
    setfig = plt.figure(figsize=(12, 6), dpi=DEFAULT_DPI)
    plt.rcParams.update({'font.size': defaultFontSize})
    ax = setfig.add_subplot(1, 1, 1)
    ax.set_title('Sets',fontsize = titlePlotFontSize)
    ax.set_xlabel("Voltage $V$ [V]", fontsize = axisLabelFontSize)
    ax.set_ylabel("Current $I$ [A]", fontsize = axisLabelFontSize)
    used_pages = []
    setCount = 0
    setSum = 0
    setSumSquared = 0
    #technically bad to iterate through rows in a columnar database
    #as it defeats their purpose, however these are small db and
    #frankly columnar is overkill for them
    for (cycle, icc, v, ron, r2, set, reset) in df.itertuples(index=False):
        if isinstance(set, int):
            page = items[set]
            labelString = f'{icc:.1f} μA'
            if cycle == 1:
                labelString += ' (form)'
            ax.plot(page.probeA_voltage, page.probeA_current, label = labelString, linewidth = LINE_WIDTH)
            ax.legend(loc='best')
            if(not math.isnan(v) and v > 0.3):
                setCount += 1
                setSum += v
                setSumSquared += v * v
    if (setCount == 0):
        print("\nMESSAGE: Due to cell having zero valid sets, expect its summary set data in Characteristics to be empty.\n")
        mean = setSum
        variance = 0
        stdDev = 0
    else:
        mean = setSum / setCount
        variance = setSumSquared / setCount - (mean * mean)
        stdDev = math.sqrt(variance)
        
    #ax.legend(loc='best')
    setfig.savefig(f'{tmpDir}/sets.png')

    resetfig = plt.figure(figsize=(12, 6), dpi=DEFAULT_DPI)
    plt.rcParams.update({'font.size': defaultFontSize})
    ax = resetfig.add_subplot(1, 1, 1)
    ax.set_title('Resets',fontsize = titlePlotFontSize)
    ax.set_xlabel("Voltage $V$ [V]", fontsize = axisLabelFontSize)
    ax.set_ylabel("Current $I$ [A]", fontsize = axisLabelFontSize)
    for (cycle, icc, v, ron, r2, set, reset) in df.itertuples(index=False):
        if isinstance(reset, int) and ron < 10000 and r2 > 0.997:
            page = items[reset]
            labelString = f'{icc:.1f} μA'
            ax.plot(page.probeA_voltage, page.probeA_current, label = labelString, linewidth = LINE_WIDTH)
            ax.legend(loc='best')
    resetfig.savefig(f'{tmpDir}/resets.png')


    summaryTableFlowable = Table(summaryTable)
    flowables.append(summaryTableFlowable)
    flowables.append(Paragraph(f'<b>Mean Set Voltage:</b> {mean}', styles['BodyText']))
    flowables.append(Paragraph(f'<b>Std Deviation:</b> {stdDev}', styles['BodyText']))
    flowables.append(__getIccRonPlot(tmpDir, df))
    flowables.append(PageBreak())
    flowables.append(__getImage(f'{tmpDir}/sets.png', PLOT_WIDTH))
    flowables.append(__getImage(f'{tmpDir}/resets.png', PLOT_WIDTH))
    flowables.append(PageBreakIfNotEmpty())

    flowables += pages

    if len(flowables) > 0:
        doc.build(flowables)

    shutil.rmtree(tmpDir)  #comment this out to keep plot images, useful when need high DPI images of plots. Not stable.  

# Name:			generatePage
# Summary:		Takes a CSV item and returns a list of flowables.
# Desc:			Does not work on observe.
#
# Input:		df, summaryTable are modified
# Output:		Flowables and df and summary table   
def __generatePage(page: CsvFile, i: int, tmpDir, df, summaryTable) -> List:
    if len(df.index) == 0:
        df.loc[0, 'Cycle'] = int(1)

    stateIndex = len(df.index) - 1
    prevStateIndex = max(0, len(df.index) - 2)
    
    df_calc = ca.calcDataFrame(page)

    # header
    styles = getSampleStyleSheet()
    flowables = [
        Paragraph(page.activity, styles["Heading2"]),
        Paragraph(f'——————————————————————————————————', styles["Heading2"])
    ]
    props = OrderedDict({
        'Time': page.timeStamp_time12hr,
        'Icc': f'{page.complianceCurrent:.1e}{page.complianceCurrentUnits}',
        'Voltage Range': f'{page.startVoltage}  →  {page.endVoltage}',
        'Target Ramp Rate': f'{page.rampRate}',
        'True Ramp Rate': f'{ca.calcRampRate(page, df_calc):.3f} V/s*',
        'Cycle': df.loc[stateIndex, 'Cycle']
    })
    reset_cell = False
    if page.activity == 'reset':
        # successful reset
        if ca.calcResistance(page, df_calc):
            resistance, r2 = ca.calcResistance(page, df_calc)

            #Is this part necessary?
            #if df.loc[stateIndex, 'Set Icc'] is None:
            #    df.loc[stateIndex, 'Set Icc'] = df.loc[prevStateIndex, 'Set Icc']
            #    df.loc[stateIndex, 'Set Voltage'] = df.loc[prevStateIndex, 'Set Voltage']

            df.loc[stateIndex, 'R_on'] = resistance
            df.loc[stateIndex, 'R2'] = r2

            props['Resistance'] = f'{resistance:.2f} Ω' #f'{state.r_on:.2f} Ω'
            props['Linear Fit R2'] = f'{r2:.3f}'

        else:
            props['Error'] = 'Too nonlinear/failed'
        if ca.calcCellState(page, df_calc) == 'reset':
            reset_cell = True
            df.loc[stateIndex, 'Reset Data'] = i
        #test code not to be merged
        ca.plot_energy(page, df_calc, f'{tmpDir}/ca_plot_energy{i}.png')
        flowables.append(__getImage(f'{tmpDir}/ca_plot_energy{i}.png', width=PLOT_WIDTH))

    else:
        # successful set/form
        #check to make sure the cell isn't already in set condition
        #by checking to make sure the set voltage isn't too low as well
        set_voltage = ca.calcSetVoltage(page, df_calc)
        if set_voltage is not None and set_voltage > 0.3:
            
            df.loc[stateIndex, 'Set Icc'] = page.complianceCurrent * 1e6
            df.loc[stateIndex, 'Set Voltage'] = set_voltage

            set_voltage = df.loc[stateIndex, 'Set Voltage']
            
            props['Set Voltage'] = f'{set_voltage:.2f} V'
            df.loc[stateIndex, 'Set Data'] = i

        elif set_voltage is None:
            props['Error'] = 'Set failed'
        else:
            props['Error'] = 'Set ran on cell that was already set'

    cycle_complete = reset_cell

    if cycle_complete:
        df.loc[len(df.index), 'Cycle'] = df.loc[stateIndex, 'Cycle'] + 1
        summaryTable.append(df.loc[stateIndex])

    # add the properties as a bulleted list
    flowables.append(ListFlowable(
        [Paragraph(f'<b>{k}:</b> {v}', styles['BodyText']) for k, v in props.items()],
        bulletType='bullet'
    ))

    # add comments from user
    flowables.append(Paragraph(page.comments, styles['BodyText']))

    # generate the plot
    plotName = f'{tmpDir}/ca_plot_{i}.png'
    ca.plot(page, df_calc, plotName)
    flowables.append(__getImage(plotName, width=PLOT_WIDTH))

    return flowables

# Name:			getImage
# Summary:		Resize image to scale.
#
# Input:		path to image, and desired width.
# Output:		Image as an object.
def __getImage(path, width=1):
    img = utils.ImageReader(path)
    iw, ih = img.getSize()
    aspect = ih / float(iw)
    return Image(path, width=width, height=(width * aspect))

# Name:			getIccRonPlot
# Summary:		Generates a PNG image of the desired plot.
#
# Input:		path, df
# Output:		Image of plot as an object.  
def __getIccRonPlot(tmpDir, df) -> Image:
    path = f"{tmpDir}/r_on_plot.png"

    fig = plt.figure(figsize=(10, 6),dpi=DEFAULT_DPI)
    fig.patch.set_facecolor('white')
    #print(df.loc[df.R2 >= 0.98, ['Set Icc', 'R_on']])
    sns.scatterplot(data=df.loc[df.R_on < 10000, :].loc[df.R2 >= 0.997 , ['Set Icc', 'R_on']], x="Set Icc", y="R_on",color = "red", edgewidth = 3)
    #sns.lineplot(data=df.loc[df.R_on < 10000, :].loc[df.R2 >= 0.997 , ['Set Icc', 'R_on']], x="Set Icc", y="R_on",estimator='max', color='black')
    plt.title("Resistance")
    plt.xlabel("$I_{cc}$ [μA]")
    plt.ylabel("$R_{on}$ [Ω]")
    plt.savefig(path)
    plt.close()

    return __getImage(path, width=PLOT_WIDTH)