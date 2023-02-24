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

#returns if CSV log file line is valid (True) or not (False)
def check_blank_line(line):
    procedure_type = line[2]
    run_num = line[6]
    array_loc = line[3]
    cell_loc = line[4]
    
    if (procedure_type != ''):
        if (array_loc != '' and cell_loc !='' and run_num !=''):
            return True
    print(f'ERROR: please check the lab note format, {line} is either invalid or missing parameters')
    return False

def check_blank_cell(str):
    changed_str = ''
    if(str == ''):
        changed_str = '?'
    else:
        changed_str = str
    return changed_str
        
def sort(line, date_in, reso_dir):
    if(check_blank_line(line)):
        #mapping
        date = line[0]
        wafer = line[1]
        procedure_type = line[2]
        array_loc = line[3]
        heat_cell_loc = line[4]
        obs_cell_loc = line[5]
        run_num = line[6]
        comment = line[7]
    
        #parse 
        if date_in == date or date_in == 'all':
            #parse activity
            activity= ''
            if((procedure_type == 'R') or (procedure_type == 'R - O') or (procedure_type == 'R - H')):  #Reset
                activity = 'reset'
            elif((procedure_type == 'S') or (procedure_type == 'S - O') or (procedure_type == 'S - H')):  #Set
                activity = 'set'
            elif(procedure_type == 'F'):  #Form
                activity = 'form'
            elif(procedure_type == 'VS' or procedure_type == 'H'or procedure_type == 'C'):  #Observe is Verify_Set, Heating, and Cooling
                activity = 'observe'
            else:
                print("ERROR: Invalid activity value found in log file.")

            #parse cell position
            wafer = check_blank_cell(wafer)
            if(wafer == '?'):
                wafer = '999'  #'?' causes errors in file open for csv! 
            else:
                wafer = int(wafer)  #expect integer index 

            if(obs_cell_loc):
                position = f'(wafer{wafer},{position_process(array_loc)},-1,-1,{position_process(heat_cell_loc)})_(wafer{wafer},{position_process(array_loc)},-1,-1,{position_process(obs_cell_loc)})'
            else:
                position = f'(wafer{wafer},{position_process(array_loc)},-1,-1,{position_process(heat_cell_loc)})'
                
            #parse runs
            icc_A = '?'  #icc for one cell, for terminal A
            icc_B = '?'  #icc for second cell
            isThreeProbe = False
            
            run_num = run_num.split(',')
            
            for num in run_num:
                num = str(num).replace(" ", "")  #remove spaces in list
                
                #parse excel workbook
                runDir = f'{reso_dir}raw_data/Run{str(num)}'  
                xlsDir = f'{runDir}/data@1[{str(num)}].xls'  
                try:
                    book = xlrd.open_workbook(xlsDir)
                    table = book.sheet_by_index(0)  #Sheet1
                    settings = book.sheet_by_index(2)  #Sheet3
                    numCols = settings.ncols
                    numRows = settings.nrows
                    
                    #parse rr/step size
                        # Step size not same thing as ramp rate!
                        # Sweeping mode vs Sampling Mode:
                        # Sampling - constant voltage, no ramp rate
                        # Sweeping - variable voltage, so ramp rate/step size valid
                    rr = ''
                    mode = settings.cell_value(2,1)  #B3
                    icc_row = -1
                    if (mode == "Sampling"):  #Step row does not exist!
                        rr = '0'  #step size is zero
                        icc_row = 18
                    elif (mode == "Sweeping"):
                        icc_row = 21
                        step_row = 19
                        if (settings.cell_value(step_row,0) == "Step"):
                            B20 = settings.cell_value(step_row,1)
                            C20 = settings.cell_value(step_row,2)  #assume 2-probe
                            if (B20 == "N/A"):
                                if (C20 == "N/A"):
                                    print(f'ERROR: Expected step size in data@1[{str(num)}].xls.')
                                else:
                                    rr = C20
                            else:
                                if (C20 != B20):
                                    print(f'ERROR: Different step sizes for two probe in data@1[{str(num)}].xls.')
                                else:
                                    rr = B20
                    
                    #parse icc
                    if (numRows > 22):
                        nameExists = False  
                        iccExists = False
                        name_row = 14
                        if (settings.cell_value(name_row,0) == "Name"):  #A15
                            nameExists = True
                        else:
                            print(f'ERROR: Could not find Name in data@1[{str(num)}].xls.')
                            
                        if (numCols > 3):  #3 probe
                            isThreeProbe = True
                            if (settings.cell_value(icc_row,0) == "Compliance"):  #A19
                                #differenciate icc for the 2 cells 
                                col_AV = -1
                                col_BV = -1
                                B15 = settings.cell_value(name_row,1)
                                C15 = settings.cell_value(name_row,2)
                                D15 = settings.cell_value(name_row,3)
                                candidates = [B15, C15, D15]
                                col_idx = 1
                                for value in candidates:
                                    if (value == "AV"):  #terminal A
                                        col_AV = col_idx
                                    elif (value == "BV"):  #terminal B
                                        col_BV = col_idx
                                    #iterate
                                    col_idx += 1
                                #find iccs
                                icc_A = settings.cell_value(icc_row,col_AV)  #in amps, ex. 6e-05, ex. 0.003
                                icc_B = settings.cell_value(icc_row,col_BV)  #in amps, ex. 6e-05, ex. 0.003
                            else:
                                print(f'ERROR: Could not find Compliance in data@1[{str(num)}].xls.')
   
                        elif (numCols > 2):  #2 probe
                            if (settings.cell_value(icc_row,0) == "Compliance"):  #A22
                                #terminal A and B will have same compliance
                                icc_A = settings.cell_value(icc_row,1)  #B19, in amps, ex. 6e-05, ex. 0.003
                                icc_B = icc_A
                            else:
                                print (f'{settings.cell_value(icc_row,0)}')
                                print(f'ERROR: Could not find Compliance in data@1[{str(num)}].xls.')
                        else:
                            print(f'ERROR: Unexpected data in data@1[{str(num)}].xls.')
                    #convert icc
                    icc_A = float(icc_A)  #use decimal.Decimal(icc) if seeing arithmetic error
                    icc_B = float(icc_B)  #use decimal.Decimal(icc) if seeing arithmetic error
                    
                    #parse time
                    time = keithley_time(runDir)
                    time = time.strftime(r'%y%m%d%H%M%S')

                    #parse vmin, vmax
                    vmin, vmax = find_min_max(table)
                    
                    #create/overwrite to csv file
                    icc = icc_A  #WARNING: only sending icc for ONE cell
                    file_name = f'{position}_{time}_{activity}_{vmin}_{vmax}_{rr}_{icc}' 
                    with open(f'{reso_dir}processed_data/{file_name}.csv', 'w', encoding='utf-8') as f:
                        write = csv.writer(f)
                        write.writerow(['---'])
                        write.writerow([comment])
                        write.writerow(['---'])
                        for row_num in range(table.nrows):
                            row_value = table.row_values(row_num)
                            write.writerow(row_value)
                    print(f'MESSAGE: {file_name} is generated successfully. Ignore the warning.')
                except:
                    print(f'ERROR: Error during CSV file generation for data@1[{str(num)}].xls.')
 
#parse lab manually populated log file AND raw data files to get information about raw data
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
