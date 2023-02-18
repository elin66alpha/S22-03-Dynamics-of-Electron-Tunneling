# Name:			keithley_import
# Summary:		.
# Refinement:   Change wafer ID to only need an integer, and therefore have much higher max. (now only has new wafer and old wafer)
#               Parse data from raw data, not log file when able.
#               Potentially, change date arg to default to "all" so make it optional arg.

import os
import argparse
import csv
import xlrd
from xml.dom.minidom import Element, parse as parse_xml
from datetime import datetime
import pytz

# (wafer2,2,10,-1,-1,2,2)_221108160418_form_0_5_1_35uA
# wf#, array#, sub#,cell#_time_operation_low_high_rr_icc

#(wafer0,0,6,-1,-1,0,3)_220401120438_form_0_5_1_30uA
#(wafer1,2,2,-1,-1,2,2)_230206145442_form_0_5_0.025_15 uA

def position_process(str):
    new_str = str.replace('(','')
    new_str = new_str.replace(')','')
    return new_str

def find_min_max(table):
    avmin = int(min(table.col_values(4 ,start_rowx=1)))
    avmax = int(max(table.col_values(4,start_rowx=1)))
    bvmin = int(min(table.col_values(2 ,start_rowx=1)))
    bvmax = int(max(table.col_values(2 ,start_rowx=1)))
    vmin = min(avmin,bvmin)
    vmax = max(avmin,bvmin)
    return vmin,vmax

def keithley_time(folder_name):
      

        xml_file = f'{folder_name}/run.xml'
        doc = parse_xml(xml_file)

        time_el: Element = doc.getElementsByTagName("Time")[0]

        s: str = time_el.firstChild.data
        s = s.replace('T', ' ')[:-1]
        s = s[:s.index('.')]

        # parse from iso after removing T and Z
        d = datetime.fromisoformat(s).replace(tzinfo=pytz.UTC)
        tz = pytz.timezone('US/Eastern')
        loc = d.astimezone(tz)

        return loc

def check_blank_line(line):
    if (line[2] == 'R' or line[2] =='S' or line[2] == 'VS' or line[2] == 'F'or line[2] == 'H'or line[2] == 'C'):
        if (line[3] != '' and line[4]!='' and line[8] !=''):
            return True
    if(line[0] != 'Date'):
        print(f'ERROR: please check the lab note format, {line} is either invalid or missing parameters')
    return False

def check_blank_cell(str):
    changed_str = ''
    if(str == ''):
        changed_str = '?'
    else:
        changed_str = str
    return changed_str
        

def sort(line, date, reso_dir):
    position= ''

    activity= ''
    time = ''
    rr = ''
    wafer = ''
    if(check_blank_line(line)):
        if line[0] == date or date == 'all':
            if(line[2] == 'R'):  #Reset
                activity = 'reset'
            elif(line[2] == 'S'):  #Set
                activity = 'set'
            elif(line[2] == 'F'):  #Form
                activity = 'form'
            elif(line[2] == 'VS' or line[2] == 'H'or line[2] == 'C'):  #Observe is Verify_Set, Heating, and Cooling
                activity = 'observe'
            else:
                print("ERROR: Invalid activity value found in log file.")

            wafer = check_blank_cell(line[1])
            if(line[1] == 'Old Wafer'):
                wafer = '0'
            elif(line[1] == 'New Wafer (Scratched)'):
                wafer = '1'
            else:
                wafer = '999'  #'?' causes errors in file open for csv!


            if(line[5]):
                position = f'(wafer{wafer},{position_process(line[3])},-1,-1,{position_process(line[4])})_(wafer{wafer},{position_process(line[3])},-1,-1,{position_process(line[5])})'
            else:
                position = f'(wafer{wafer},{position_process(line[3])},-1,-1,{position_process(line[4])})'
            icc = check_blank_cell(line[6]).replace(' ','')
            rr =  check_blank_cell(line[7])
            run_num = line[8].split(',')
            
            for num in run_num:
                num = str(num).replace(" ", "")  #remove spaces in list
                
                runDir = f'{reso_dir}raw_data/Run{str(num)}'  
                xlsDir = f'{runDir}/data@1[{str(num)}].xls'  
                try:
                    raw = xlrd.open_workbook(xlsDir)
                    time = keithley_time(runDir)
                    time = time.strftime(r'%y%m%d%H%M%S')
                    table = raw.sheet_by_index(0)
                    vmin, vmax= find_min_max(table)
                    file_name = f'{position}_{time}_{activity}_{vmin}_{vmax}_{rr}_{icc}'
                    #create/overwrite csv file
                    with open(f'{reso_dir}processed_data/{file_name}.csv', 'w', encoding='utf-8') as f:
                        write = csv.writer(f)
                        write.writerow(['---'])
                        write.writerow([line[9]])
                        write.writerow(['---'])
                        for row_num in range(table.nrows):
                            row_value = table.row_values(row_num)
                            write.writerow(row_value)
                    print(f'MESSAGE: {file_name} is generated successfully. Ignore the warning.')
                except:
                    print(f'ERROR: {file_name} was not generated.')
 
#parse lab manually populated log file to get information about raw data
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('log_file_name', type=str)
    parser.add_argument('date', type=str)
    args = parser.parse_args()
    
    curDir = os.getcwd()  #current working directory
    curDir = curDir.replace("\\", "/")
    resourcesDir = curDir + "/resources/"
    logFile = resourcesDir + "raw_data/" + args.log_file_name + ".csv"

    csv_reader = csv.reader(open(logFile, newline = ''))  #set newline to prevent /r/n /n conflicts
    i = 0
    for line in csv_reader:
        if (i > 0):  #skip header row
            sort(line, args.date, resourcesDir)
        i = i + 1
