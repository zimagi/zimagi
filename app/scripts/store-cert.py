#!/usr/bin/env python
#-------------------------------------------------------------------------------
import sys
import re
#-------------------------------------------------------------------------------

file_path = sys.argv[1]
content = sys.argv[2]

matches = re.search(r'^(\-+\s+[^\-]+\s+\-+)\s+(.+)\s+(\-+\s+[^\-]+\s+\-+)$', content)
key_prefix = matches.group(1)
key_material = matches.group(2)
key_suffix = matches.group(3) 

with open(file_path, 'w') as file:
    file.write("{}\n{}\n{}".format(
        key_prefix, 
        key_material, 
        key_suffix
    ))
