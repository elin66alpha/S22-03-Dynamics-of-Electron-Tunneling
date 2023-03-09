# Name:			generateReport.py
# Summary:		.
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
import matplotlib.pyplot as plt
import seaborn as sns

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image, PageBreakIfNotEmpty, Table, ListFlowable
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import utils

import src.CellAnalyzer as ca
from src.utils.CsvFile import CsvFile

            
# Name:			.
# Summary:		.
# Desc:			Generates a PDF file and outputs a pdf in the folder path.
# Refinement:	.
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
    
    tmpDir = f'{pdfFolder}/tmp'
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
            print(df)
            pages.append(flowable)
        
        # put each operation on its own page
        if i < len(items) - 1:
            pages.append(PageBreakIfNotEmpty())
    
    setfig = plt.figure(figsize=(10, 4), dpi=300)
    plt.title('Sets')
    plt.xlabel("Voltage $V$ [V]")
    plt.ylabel("Current $I$ [A]")
    for i, page in enumerate(items):
        if page.activity == 'set':
            plt.plot(page.probeA_voltage, page.probeA_current)
    plt.savefig(f'{tmpDir}/sets.png')

    resetfig = plt.figure(figsize=(10, 4), dpi=300)
    plt.title('Resets')
    plt.xlabel("Voltage $V$ [V]")
    plt.ylabel("Current $I$ [A]")
    for i, page in enumerate(items):
        if page.activity == 'reset':
            plt.plot(page.probeA_voltage, page.probeA_current)
    plt.savefig(f'{tmpDir}/resets.png')


    summaryTableFlowable = Table(summaryTable)
    flowables.append(summaryTableFlowable)
    flowables.append(__getIccRonPlot(tmpDir, df))
    flowables.append(__getImage(f'{tmpDir}/sets.png', 600))
    flowables.append(__getImage(f'{tmpDir}/resets.png', 600))
    flowables.append(PageBreakIfNotEmpty())

    flowables += pages

    if len(flowables) > 0:
        doc.build(flowables)

    shutil.rmtree(tmpDir)   

# Name:			.
# Summary:		.
# Desc:			Takes a CSV item and returns a list of flowables. Does not work on observe.
# Refinement:	Check if changing states to regular variables is fine
#
# Input:		
#               df, summaryTable are modified
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
    #print(page.csvFileName)
    #print(page.complianceCurrent)
    #print()
    props = OrderedDict({
        'Time': page.timeStamp_time12hr,
        'Icc': f'{page.complianceCurrent:.1f}{page.complianceCurrentUnits}',
        'Voltage Range': f'{page.startVoltage}  →  {page.endVoltage}',
        'Target Ramp Rate': f'{page.rampRate}',
        'True Ramp Rate': f'{ca.calcRampRate(page, df_calc):.3f} V/s*',
        'Cycle': df.loc[stateIndex, 'Cycle']#state.cycle
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
        flowables.append(__getImage(f'{tmpDir}/ca_plot_energy{i}.png', width=400))

    else:
        # successful set/form
        if ca.calcSetVoltage(page, df_calc):
            df.loc[stateIndex, 'Set Icc'] = page.complianceCurrent
            df.loc[stateIndex, 'Set Voltage'] = ca.calcSetVoltage(page, df_calc)

            set_voltage = df.loc[stateIndex, 'Set Voltage']

            props['Set Voltage'] = f'{set_voltage:.2f} V'
            df.loc[stateIndex, 'Set Data'] = i

        else:
            props['Error'] = 'Set failed'


    cycle_complete = reset_cell

    if cycle_complete:
        df.loc[len(df.index), 'Cycle'] = df.loc[stateIndex, 'Cycle'] + 1
        print(df)
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
    flowables.append(__getImage(plotName, width=400))

    return flowables

# Name:			.
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

# Name:			.
# Summary:		.
# Desc:			.
# Refinement:	.
#
# Input:		.
# Output:		.  
def __getIccRonPlot(tmpDir, df) -> Image:
    path = f"{tmpDir}/r_on_plot.png"

    fig = plt.figure(dpi=300)
    fig.patch.set_facecolor('white')
    print(df)
    #print(df.loc[df.R2 >= 0.98, ['Set Icc', 'R_on']])
    sns.scatterplot(data=df.loc[df.R_on < 10000, :].loc[df.R2 >= 0.9999 , ['Set Icc', 'R_on']], x="Set Icc", y="R_on")
    plt.title("Resistance")
    plt.xlabel("$I_{cc}$ [μA]")
    plt.ylabel("$R_{on}$ [Ω]")
    plt.savefig(path)
    plt.close()

    return __getImage(path, width=400)