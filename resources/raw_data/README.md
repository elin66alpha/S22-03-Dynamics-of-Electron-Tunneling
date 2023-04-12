## Overview

Input raw data files go here.

> Remember, there cannot be duplicate run numbers within a folder. Though this should not happen, it requires processing the data separately. 

## Instructions

Into this (top) directory...
1. Move your log file (must be .csv). If necessary, convert it.

> Notice the example log file's legend. 

2. Move your raw data.

> On the Keithley machine, raw data folders are named: `TestName_ClariusProjectName`.

3. Rename each folder to the `Op Code` corresponding to its `Test Name`, referring to the aforementioned legend.

> Ex. `Cooling_Doet -> C`

> Note: If a Clarius project is created or modified, therefore requiring an updated legend, this software may not perform as expected. As, support has to be added for the modification. 

## Example Directory

README.md

log.csv

-S

--Run1

---data@1[1].xls

---run.xml

---etc...

-VS

--Run27

---data@1[27].xls

---run.xml

---etc...

-H

--Run12

---data@1[12].xls

---run.xml

---etc...

-RP

--Run108

---data@1[108].xls

---run.xml

---etc...