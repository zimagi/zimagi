#!/usr/bin/env python
#-------------------------------------------------------------------------------
import sys
import re
#-------------------------------------------------------------------------------

file_path = sys.argv[1]
components = re.search(r'^(\-+[^\-]+\-+)\s+(.+)\s+(\-+[^\-]+\-+)$', sys.argv[2])

if components:
    key_prefix = components.group(1)
    key_material = "\n".join(re.split(r'\s+', components.group(2)))
    key_suffix = components.group(3)
else:
    raise Exception('Key entered is not correct format') 

with open(file_path, 'w') as file:
    file.write("{}\n{}\n{}".format(
        key_prefix, 
        key_material, 
        key_suffix
    ))
