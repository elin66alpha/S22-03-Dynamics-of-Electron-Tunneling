# Name:			.
# Summary:		.
#
# Creator: 		Mihir Savadi

from lib import *

from utils.csvParser import csvParser
from utils.csvItem import csvItem
from utils.base import dataBaseCollator
from pdfGenerator.pdfgen import pdfGen

if __name__ == "__main__":

    now = datetime.now()
    timeFormat = "%Y-%b-%d-%I%M%p_%Ss"

    # simply instantiate a dataBaseCollator object and the report files will be created
    db = dataBaseCollator('./resources/processed_data/', f'./resources/analysis_reports/report_{now.strftime(timeFormat)}/')