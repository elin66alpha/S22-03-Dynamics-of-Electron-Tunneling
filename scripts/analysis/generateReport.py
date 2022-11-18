# Name:			generate_reports.py
# Summary:		.
# Desc:         .
#
# Creator: 		Jim Furches

# Name:			CellAnalyzerReport
# Summary:		Datatype for a pdf report.
# Desc:			Takes in CSV files, analyzes the properties of the cells using the CellAnalyzer, and creates a special pdf report containing that information.
#   
# Limitations:  Currently only supports 2-probe measurements.
# Refinement:	Remove this datatype. Convert to methods to generate the reports.

from dataclasses import dataclass

import pandas
from resistanceAnalyzer.cellanalyzer import CellAnalyzer
from utils.csvItem import csvItem

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image, PageBreakIfNotEmpty, Table, ListFlowable
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import utils

from typing import Iterable, Dict, List, OrderedDict

import matplotlib.pyplot as plt
import seaborn as sns

import os
import shutil

# Name:			ProcessState
# Summary:		Datatype for __.
# Desc:			.
#       
# Refinement:	.
@dataclass
class ProcessState:
    cycle: int
    set_icc: str
    set_voltage: float
    r_on: float
    r2: float

    def is_complete_cycle(self):
        return self.cycle \
            and self.set_icc \
            and self.set_voltage \
            and self.r_on \
            and self.r2
            
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
def generateReport(csvItems: List[csvItem], summaryDict: Dict[str, object], pdfFolder: str):
    #init
    cellCoord = csvItems[0].targetCellCoord
    pdfFolder = pdfFolder
    pdf_name = f"{pdfFolder}/({cellCoord})_characteristics.pdf"

    items = csvItems

    cellSummaryDict = summaryDict[cellCoord]
    cellSize = cellSummaryDict['cellSize']
    timesAccessed = cellSummaryDict['timesAccessed']
    lastAccessed = cellSummaryDict['lastAccessed']

    df = pandas.DataFrame(columns=['Cycle', 'Set Icc', 'Set Voltage', 'R_on', 'R2'])
    summaryTable = [["Cycle #", "Set Icc (μA)", "Set Voltage (V)", "R_on (Ω)", "R2"]]
    
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
            pages.append(flowable)
        
        # put each operation on its own page
        if i < len(items) - 1:
            pages.append(PageBreakIfNotEmpty())
    
    summaryTableFlowable = Table(summaryTable)
    flowables.append(summaryTableFlowable)
    flowables.append(__getIccRonPlot(tmpDir, df))
    flowables.append(PageBreakIfNotEmpty())

    flowables += pages

    if len(flowables) > 0:
        doc.build(flowables)

    shutil.rmtree(tmpDir)   


# Name:			.
# Summary:		.
# Desc:			Takes a CSV item and returns a list of flowables. Does not work on observe.
# Refinement:	Make sure changing states to reg variables is fine
#
# Input:		
#               df, summaryTable are modified
# Output:		Flowables and df and summary table   
def __generatePage(page: csvItem, i: int, tmpDir, df, summaryTable) -> List:
    #init
    #df_copy = df  #need to deepcopy?
    
    state = ProcessState(1, None, None, None, None)
    prevState = state
    
    ca = CellAnalyzer(page)

    # header
    styles = getSampleStyleSheet()
    flowables = [
        Paragraph(ca.activity(), styles["Heading2"]),
        Paragraph(f'——————————————————————————————————', styles["Heading2"])
    ]

    props = OrderedDict({
        'Time': page.timeStamp_time12hr,
        'Icc': f'{page.complianceCurrent:.1f}{page.complianceCurrentUnits}',
        'Voltage Range': f'{page.startVoltage}  →  {page.endVoltage}',
        'Target Ramp Rate': f'{page.rampRate}',
        'True Ramp Rate': f'{ca.ramp_rate:.3f} V/s*',
        'Cycle': state.cycle
    })

    if ca.activity() == 'reset':
        # successful reset
        if ca.resistance:
            state.r_on = ca.resistance
            state.r2 = ca.r2

            if state.set_icc is None:
                state.set_icc = prevState.set_icc
                state.set_voltage = prevState.set_voltage

            props['Resistance'] = f'{ca.resistance:.2f} Ω'
            props['Linear Fit R2'] = f'{ca.r2:.3f}'
        
        else:
            props['Error'] = 'Too nonlinear/failed'
        
        #test code not to be merged
        ca.plot_energy(f'{tmpDir}/ca_plot_energy{i}.png')
        flowables.append(__getImage(f'{tmpDir}/ca_plot_energy{i}.png', width=400))

    else:
        # successful set/form
        if ca.set_voltage:
            state.set_icc = page.complianceCurrent
            state.set_voltage = ca.set_voltage

            props['Set Voltage'] = f'{ca.set_voltage:.2f} V'

        else:
            props['Error'] = 'Set failed'
    
    if state.is_complete_cycle():
        df = df.append({
            'Cycle': state.cycle,
            'Set Icc': state.set_icc,
            'Set Voltage': state.set_voltage,
            'R_on': state.r_on,
            'R2': state.r2
        }, ignore_index=True)
        summaryTable.append([state.cycle, state.set_icc, f'{state.set_voltage:.2f}', f'{state.r_on:.2f}', f'{state.r2:.3f}'])
        prevState = state
        state = ProcessState(state.cycle + 1, None, None, None, None)

    # add the properties as a bulleted list
    flowables.append(ListFlowable(
        [Paragraph(f'<b>{k}:</b> {v}', styles['BodyText']) for k, v in props.items()],
        bulletType='bullet'
    ))

    # add comments from user
    flowables.append(Paragraph(page.comments, styles['BodyText']))

    # generate the plot
    plotName = f'{tmpDir}/ca_plot_{i}.png'
    ca.plot(plotName)
    flowables.append(__getImage(plotName, width=400))

    return flowables

# Name:			.
# Summary:		.
# Desc:			.
# Refinement:	.
#
# Input:		.
# Output:		.
def __getImage(path, width=1):
    """Makes resizing images to scale easy
    """
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
    sns.scatterplot(data=df.loc[df.R2 >= 0.98, :], x="Set Icc", y="R_on")
    plt.title("Resistance")
    plt.xlabel("$I_{cc}$ [μA]")
    plt.ylabel("$R_{on}$ [Ω]")
    plt.savefig(path)
    plt.close()

    return __getImage(path, width=400)