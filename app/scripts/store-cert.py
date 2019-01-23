#!/usr/bin/env python
#-------------------------------------------------------------------------------
import sys
#-------------------------------------------------------------------------------

file_path = sys.argv[1]
content = sys.argv[2]


with open(file_path, 'w') as file:
    file.write(content)
