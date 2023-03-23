# Impact of Thermal Cross-talk on Bit Immunity - Central Repository

Previously named "Dynamics of Electron Tunneling."

Sponsored by Micron Technology, Inc.

## Project Summary

To design and execute an experimental and data acquisition methodology to observe and alter memory cells in ReRAM arrays, to investigate thermal cross-talk’s impact on the reliability of a heated and neighboring cell. The proposed approach aims to create a structured framework for conducting research on ReRAM cells more efficiently and effectively.

### Previous Work
We are continuing a previous team's work; credit goes to them. Among other things, the previous team discovered a crucial case of unexpected behavior. A spontaneous set of a neighboring cell.  
<div style="text-align: center;">

[Git Repository](https://github.com/mihirsavadi/MicronDynamicsOfElectronTunneling)
</div>
	
### Goal
To capture (measure) aforementioned unexpected behavior, then explore limits of neighboring cell.

## Overview
This repo serves to make data analysis and its interactions efficient. Thus, increasing the efficiency of both data collection and review.

### Procedure
1. Process raw measurement data.
2. Analyze/plot processed measurement data.

## Instructions
> For detailed instructions on how to use this repo to analyze measurement data, see `INSTRUCTIONS.txt`.
	
## Developer Notes
> For detailed guidelines, see `internal_guidelines.txt`. 

## Workflow
The `main` branch always contains stable code. The `dev` branch contains potentially unstable code. To make changes, developers branch off `dev` with `their_name/task_summary`. `dev` is merged with `main` periodically, after verifying its stability. 

```mermaid
gitGraph
	commit
	commit
	branch dev
	commit

	branch name/task_summary
	commit
	
	checkout dev
	branch another_name/task_summary
	commit
	commit
	checkout dev
	
	checkout name/task_summary
	commit
	checkout dev
	merge name/task_summary
	
	checkout another_name/task_summary
	commit
	checkout dev
	merge another_name/task_summary
	
	checkout main
	merge dev
```

## Cell Mapping

### Wafer Mask
![An illustration of the wafer mask](/images/mask.jpg)

### Cut Wafer
During manufacturing, the wafer is cut in half, to focus data collection on the northern (topmost) quadrant of the mask. Thus, our arrays and naming convention only coincide with this portion.
![An illustration of the cut wafer](/images/cutwafer.jpg)

### Grid Coordinate System
![An illustration of the grid coordinate system](/images/maskcoord.jpg)
![An illustration of cell array indexing](/images/array_indexing.png)
![An illustration of cell array](/images/cell_array.png)

> Cells are indexed starting from 0, going left to right and down to up. So, from (0, 0) to (4, 4)

![An illustration of cell construction](/images/cell_side_view.png)

> Notice the copper filament through TaOx. This is what "Dynamics of Electron Tunneling" refers to. It is conductive (a short) when the cell is in Set state, and ruptured (a break) when the cell is in Reset state.

### Naming Convention
The cell naming convention used.

> Generated analysis reports are organized by cell (location). Thus, use this convention to interpret the file names.

location(cell<sub>i</sub>) = (d<sub>0</sub>, r<sub>0</sub>, c<sub>0</sub>, r<sub>1</sub>, c<sub>1</sub>, r<sub>2</sub>, c<sub>2</sub>) 
&ensp;where d<sub>0</sub> is device type. 
&ensp;where r<sub>0</sub> is the primary row number (the red number in Grid) 
&ensp;where c<sub>0</sub> is the primary column number (the green number in Grid) 
&ensp;where r<sub>1</sub> is the secondary row number (the blue number in Grid) 
&ensp;where c<sub>1</sub> is the secondary column number (the yellow number in Grid) 
&ensp;where r<sub>2</sub> is the row of the cell in the array defined by (d<sub>0</sub>, r<sub>0</sub>, c<sub>0</sub>, r<sub>1</sub>, c<sub>1</sub>) 
&ensp;where c<sub>2</sub> is the column of the cell in the array defined by (d<sub>0</sub>, r<sub>0</sub>, c<sub>0</sub>, r<sub>1</sub>, c<sub>1</sub>)

> For now, secondary cell location will always be (-1, -1), as we are not using those arrays.
