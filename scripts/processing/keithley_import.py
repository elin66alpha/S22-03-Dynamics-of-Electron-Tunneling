# Name:			keithley_import
# Summary:		Process raw data into CSVs.
# Desc:         Be wary of excel binary and excel formatting, such as utf8 vs utf16.
# Refinement:   Parse data from raw data, not log file when able.
#               Potentially, change date arg to default to "all" so make it optional arg.
#               Make functions for some code from "sort" for maintainability. 

import os
import argparse
import csv
import xlrd
from xml.dom.minidom import Element, parse as parse_xml
from datetime import datetime
import pytz

#maps excel cell numbers as per log file formatting standard
#input: line/row of excel file 
class LogRow:
    def __init__(self, line):
        #mapping
        self.date = line[0]
        self.wafer = line[1]
        self.procedure_type = line[2]
        self.array_loc = line[3]
        self.heat_cell_loc = line[4]
        self.obs_cell_loc = line[5]
        self.run_num = line[6]
        self.comment = line[7]
    
    #all valid cells in line are blank. aka ignore the legend.
    def allBlank(self):
        if (self.date  == '') and (self.wafer  == '') and (self.procedure_type  == '') and (self.array_loc  == '') and (self.heat_cell_loc  == '') and (self.obs_cell_loc  == '') and (self.run_num  == '') and (self.comment  == ''):
            return True
        return False
    
    def getProcedureActivity(self):
        activity = ''
        if((self.procedure_type == 'R') or (self.procedure_type == 'R - O') or (self.procedure_type == 'R - H') or (self.procedure_type == 'RH') or (self.procedure_type == 'RP')):  #Reset
            activity = 'reset'
        elif((self.procedure_type == 'S') or (self.procedure_type == 'S - O') or (self.procedure_type == 'S - H')) or (self.procedure_type == 'SH') or (self.procedure_type == 'SP'):  #Set
            activity = 'set'
        elif(self.procedure_type == 'F'):  #Form
            activity = 'form'
        elif(self.procedure_type == 'VS' or self.procedure_type == 'H'or self.procedure_type == 'C'):  #Observe is Verify_Set, Heating, and Cooling
            activity = 'observe'
        else:
            print("ERROR: Invalid activity value found in log file.")
        return activity
    
    #for when want to print(LogRow_obj)
    def getPrintableString(self):
        return self.__dict__

def remove_parenthesis(str):
    new_str = str.replace('(','')
    new_str = new_str.replace(')','')
    return new_str

def find_min_max(table):
    avmin = int(min(table.col_values(4 ,start_rowx=1)))  #verify this only skips header row
    avmax = int(max(table.col_values(4, start_rowx=1)))
    bvmin = int(min(table.col_values(2 ,start_rowx=1)))
    bvmax = int(max(table.col_values(2 ,start_rowx=1)))
    vmin = min(avmin,bvmin)
    vmax = max(avmax,bvmax)
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

#does not contain thorough validity checking
#contains error handling 
#Refinement: move to class method
#returns if CSV log file line is valid (True) or not (False)
#input: LogRow object
def check_blank_line(ln):
    # begin started to implement support for log file having 1st cell location always as heated, and 2nd cell location always as observed  
    #cell_loc = ln.heat_cell_loc
    #if(cell_loc == ''):
    #    ln.heat_cell_loc = ln.obs_cell_loc  #takes the second cell location as the first cell location.
    #    cell_loc = ln.heat_cell_loc
    # end started to implement...
    
    if (ln.allBlank()):  #ignore lines with blank cells simply because legend is longer than data to process
        #skip line, no error
        return False
    elif (ln.procedure_type != ''):  #check for cells that must always be populated 
        if (ln.array_loc != '' and ln.heat_cell_loc !='' and ln.run_num !=''):  #
            return True
    
    #treat every other case as an error
    print(f'ERROR: Please check the lab note format, {ln.getPrintableString()} is either invalid or missing parameters.')
    return False
    
# Input: integers    
# Output: True when valid location
def isValidArrayLocation(row, col):
    isErr = False
    if (row < 0) or (row > 4):
        isErr = True
    elif (col < 0) or (col > 15):
        isErr = True
    return not isErr   

# Input: integers    
# Output: True when valid location
def isValidCellLocation(row, col):
    isErr = False
    if (row < 0) or (row > 4):
        isErr = True
    elif (col < 0) or (col > 4):
        isErr = True
    return not isErr     
            
def check_blank_cell(str):
    changed_str = ''
    if(str == ''):
        changed_str = '?'
    else:
        changed_str = str
    return changed_str
        
def sort(line, date_in, reso_dir):
    ln = LogRow(line)  #mapping
    lnValid = check_blank_line(ln)
    if (lnValid):
        #parse 
        if date_in == ln.date or date_in == 'all':
            #parse cell locations, error handling 
            array_loc = ln.array_loc            
            loc = remove_parenthesis(array_loc).split(',')
            valid = isValidArrayLocation(int(loc[0]), int(loc[1]))
            if not valid:
                print(f'ERROR: Encountered unexpected cell array coordinate {array_loc} in sort. Using placeholder (-1,-1) for CSV.')
                array_loc = '-1,-1'
            heat_cell_loc = ln.heat_cell_loc
            loc = remove_parenthesis(heat_cell_loc).split(',')
            valid = isValidCellLocation(int(loc[0]), int(loc[1]))
            if not valid:
                print(f'ERROR: Encountered unexpected cell coordinate {heat_cell_loc} in sort. Using placeholder (-1,-1) for CSV.')
                heat_cell_loc = '-1,-1'
            obs_cell_loc = ln.obs_cell_loc
            if (obs_cell_loc != ''):  #obs cell can be empty and valid
                loc = remove_parenthesis(obs_cell_loc).split(',')
                valid = isValidCellLocation(int(loc[0]), int(loc[1]))
                if not valid:
                    print(f'ERROR: Encountered unexpected cell coordinate {obs_cell_loc} in sort. Using placeholder (-1,-1) for CSV.')
                    obs_cell_loc = '-1,-1'
                
            #parse activity
            activity = ln.getProcedureActivity()

            #parse cell position
            wafer = check_blank_cell(ln.wafer)
            if(wafer == '?'):
                wafer = '999'  #'?' causes errors in file open for csv! 
            else:
                wafer = int(wafer)  #expect integer index 
            #assume 3-probe/terminal when log file has both cell locations populated (when log file is correct)
            if(obs_cell_loc):
                position = f'(wafer{wafer},{remove_parenthesis(array_loc)},-1,-1,{remove_parenthesis(heat_cell_loc)})_(wafer{wafer},{remove_parenthesis(array_loc)},-1,-1,{remove_parenthesis(obs_cell_loc)})'
            else:
                position = f'(wafer{wafer},{remove_parenthesis(array_loc)},-1,-1,{remove_parenthesis(heat_cell_loc)})'
                
            #parse runs
            icc_A = ''  #icc for one cell, for terminal A
            icc_B = ''  #icc for second cell
            isThreeProbe = False
            
            run_num = ln.run_num.split(',')
            
            for num in run_num:
                num = str(num).replace(" ", "")  #remove spaces in list
                
                #parse excel workbook
                runDir = f'{reso_dir}raw_data/'
                runDir += ln.procedure_type
                runDir += '/Run'+str(num)
                print(str(runDir))
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
                    rr_invalid = False
                    icc_row = -1
                    if (mode == "Sampling"):  #Step row does not exist!
                        rr_invalid = True
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
                    device_terminal_row = 12
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
                            if (settings.cell_value(icc_row,0) == "Compliance"):
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
   
                        elif (numCols > 2):  #2 probe means 1 cell so only looking for 1, any, Icc
                            if (settings.cell_value(icc_row,0) == "Compliance"):
                                #ID columns for terminal A, B, and C
                                col_icc = -1
                                B13 = settings.cell_value(device_terminal_row,1)
                                C13 = settings.cell_value(device_terminal_row,2)
                                candidates = [B13, C13]
                                col_idx = 1
                                for value in candidates:
                                    if not (value == "C"):  #assume C is ground aka GNDU
                                        if (value == "A") or (value == "B"):
                                            col_icc = col_idx
                                    #iterate
                                    col_idx += 1
                                #done
                                icc_A = settings.cell_value(icc_row,col_icc)  #in amps, ex. 6e-05, ex. 0.003
                                icc_B = settings.cell_value(icc_row,col_icc)
                            else:
                                print (f'{settings.cell_value(icc_row,0)}')
                                print(f'ERROR: Could not find Compliance in data@1[{str(num)}].xls.')
                        else:
                            print(f'ERROR: Unexpected data in data@1[{str(num)}].xls.')
                    
                    #convert icc
                    if (icc_A == "N/A"):
                        icc_A = 0
                        print(f'WARNING: Grabbed N/A as terminal A Icc for data@1[{str(num)}].xls.')
                    else:
                        icc_A = float(icc_A)  #use decimal.Decimal(icc) if seeing arithmetic error
                    if (icc_B == "N/A"):
                        icc_B = 0
                        print(f'WARNING: Grabbed N/A as terminal B Icc for data@1[{str(num)}].xls.')
                    else:
                        icc_B = float(icc_B)  #use decimal.Decimal(icc) if seeing arithmetic error

                    #parse time
                    time = keithley_time(runDir)
                    time = time.strftime(r'%y%m%d%H%M%S')
                    
                    #parse vmin, vmax,, only valid when rr valid 
                    if (rr_invalid):
                        vmin = 0
                        vmax = 0
                    else:
                        vmin, vmax = find_min_max(table)
                    
                    #create/overwrite to csv file
                    icc = icc_A  #WARNING: only sending icc for ONE cell
                    file_name = f'{position}_{time}_{activity}_{vmin}_{vmax}_{rr}_{icc}' 
                    with open(f'{reso_dir}processed_data/{file_name}.csv', 'w', encoding='utf-8') as f:
                        write = csv.writer(f)
                        write.writerow(['---'])
                        write.writerow([ln.comment])
                        write.writerow(['---'])
                        titleRow = table.row_values(0)
                        for row_num in range(table.nrows):
                            row_value = table.row_values(row_num)
                            if (isValidTableRow(row_value, titleRow)):  #skip incomplete data
                                write.writerow(row_value)
                    print(f'MESSAGE: {file_name} is generated successfully. Ignore the warning.\n')
                except:
                    print(f'ERROR: Error during CSV file generation for data@1[{str(num)}].xls.')


#checks data in Sheet 1 of XLS file for corruption (unexpected blanks)
def isValidTableRow(row, titleRow):
    if (row == titleRow):
        return True
    #when part of a line is blank (not entire line), skip processing that line
    else:
        expectedColNum = len(titleRow)
        actualColNum = len(row)  #same as expected
        #count blank cells
        for cell in row:
            if (cell == ''):
                actualColNum -= 1
        if (actualColNum != expectedColNum):
            return False
    return True
 
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
