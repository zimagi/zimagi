#!/usr/bin/env python
#-------------------------------------------------------------------------------
import sys
import os
import re

script_path = os.path.dirname(os.path.realpath(__file__))
cert_path = os.path.join(script_path, '..', 'certs')
#-------------------------------------------------------------------------------

key_file = sys.argv[1]
components = re.search(r'^(\-+[^\-]+\-+)\s+(.+)\s+(\-+[^\-]+\-+)$', sys.argv[2])

if components:
    key_prefix = components.group(1)
    key_material = "\n".join(re.split(r'\s+', components.group(2)))
    key_suffix = components.group(3)
else:
    raise Exception("Key {} entered is not correct format: {}".format(key_file, sys.argv[2])) 

with open(os.path.join(cert_path, key_file), 'w') as file:
    file.write("{}\n{}\n{}".format(
        key_prefix, 
        key_material, 
        key_suffix
    ))
