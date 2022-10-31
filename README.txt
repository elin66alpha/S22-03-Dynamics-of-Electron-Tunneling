# Name:			README.txt
# Summary:		Dev guidelines
# Desc:			Contains internal guidelines, containing everything a scripter needs to know to use, maintain, and expand code.
#
#				Due to differences in file formatting, such as indents, Notepad++ is recommended when viewing both scripts and guidelines.
#
# Created: 		Oct. 27th, 2022, Risa Philpott
# Last Edited: 	Oct. 31st, 2022, Risa Philpott

ORGANIZATION

Datatype Structure
	


GUIDELINES

Overview
  Analyzing measurement data is performed as two-step process. 

  1. Process raw measurement data.
	   - [NEW] Format raw files as necessary, then convert to a custom datatype(s).
	   - [OG] Convert raw files to a custom datatype.
  2. Analyze processed measurement data.   
	   - "Input" must be custom datatype(s).
	   - Create data analysis reports.

Limitations (Might delete)
  List any internal restrictions or requirements (regarding the entire repo) here, such as python version compatibilty.

Known Issues
  - in cvsParser.py, on Windows,
		"file = open(csvPath, 'r')" -> "file = open(csvPath, 'r', encoding = 'utf8')"


TEMPLATES

Files

# Name:			.
# Summary:		.
#
# Created: 		.
# Last Edited: 	.

Methods, Classes, etc

# Name:			.
# Summary:		.
# Desc:			.
# Maintenance:	.
# Limitations:	.
# Refinement:	.
#
# Input:		.
# Output:		.

# Name:			.
# Summary:		.
# Desc:			.
# Refinement:	.
#
# Input:		.
# Output:		.