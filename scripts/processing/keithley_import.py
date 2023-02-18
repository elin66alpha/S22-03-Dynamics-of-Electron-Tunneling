
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
        print(f'ERROR: please check the lab note format, {line} is missing parameters')
    return False

def check_blank_cell(str):
    changed_str = ''
    if(str == ''):
        changed_str = '?'
    else:
        changed_str = str
    return changed_str
        

def sort(line,date):

    folder_name = ''
    position= ''

    activity= ''
    time = ''
    rr = ''
    wafer = ''
    if(check_blank_line(line)):
        if line[0] == date or date == 'all':
            folder_name = line[2]
            if(line[2] == 'R'):
                activity = 'reset'
            elif(line[2] == 'S'):
                activity = 'set'
            elif(line[2] == 'F'):
                activity = 'form'
            elif(line[2] == 'VS' or line[2] == 'H'or line[2] == 'C'):
                activity = 'observe'

            wafer = check_blank_cell(line[1])
            if(line[1] == 'Old Wafer'):
                wafer = '0'
            elif(line[1] == 'New Wafer (Scratched)'):
                wafer = '1'
            else:
                wafer = '?'


            if(line[5]):
                position = f'(wafer{wafer},{position_process(line[3])},-1,-1,{position_process(line[4])})_(wafer{wafer},{position_process(line[3])},-1,-1,{position_process(line[5])})'
            else:
                position = f'(wafer{wafer},{position_process(line[3])},-1,-1,{position_process(line[4])})'
            icc = check_blank_cell(line[6]).replace(' ','')
            rr =  check_blank_cell(line[7])
            run_num = line[8].split(',')
            for num in run_num:
                try:
                    raw = xlrd.open_workbook(
                        f'{folder_name}/Run{str(num)}/data@1[{str(num)}].xls')
                    time = keithley_time(f'{folder_name}/Run{str(num)}')
                    time = time.strftime(r'%y%m%d%H%M%S')
                    table = raw.sheet_by_index(0)
                    vmin, vmax= find_min_max(table)
                    file_name = f'{position}_{time}_{activity}_{vmin}_{vmax}_{rr}_{icc}'
                    
                    with open(f'orgnized/{file_name}.csv', 'w', encoding='utf-8') as f:
                        write = csv.writer(f)
                        write.writerow(['---'])
                        write.writerow([line[9]])
                        write.writerow(['---'])
                        for row_num in range(table.nrows):
                            row_value = table.row_values(row_num)
                            write.writerow(row_value)
                    print(f'MESSAGE: {file_name} is generated successfully. Ignore the warning.')
                except:
                    print( f'ERROR: {folder_name}/Run{str(num)}/data@1[{str(num)}].xls is not found')
 

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('log_file', type=str)
    parser.add_argument('date', type=str)
    args = parser.parse_args()
 
    try:
        os.makedirs('orgnized')
    except FileExistsError:
        pass

    csv_reader = csv.reader(open(args.log_file))
    for line in csv_reader:
        sort(line,args.date)
