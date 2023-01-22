# Name:			.
# Summary:		.
# Refinement:   Make dirs cmd line arguments?
#               Argument for selecting three or two probe 

#import dependencies
from datetime import datetime
import src.analysisWrapper as a 

#store current date and time 
now = datetime.now()
timeFormat = "%Y-%b-%d-%I%M%p_%Ss"

#set dirs
input_data_path = "./resources/processed_data/"
output_report_path = f'./resources/analysis_reports/report_{now.strftime(timeFormat)}/'

#perform analysis 

#data for all csv files in path
csvData = a.convert_csv_files(input_data_path)  

#generate pdf reports for csv files 
a.generate_reports(output_report_path, csvData)
    
    
    
#if __name__ == "__main__":  #ensures this code will not be ran when this script file is imported by another script

#using a "__main__.py" lets you simply name the directory or zipfile on the command line:
# $ python my_program_dir
# $ python my_program.zip
# # Or, if the program is accessible as a module
# $ python -m my_program