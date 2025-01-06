#!/usr/bin/env python3
# -------------------------------------------------------------------------------
import os
import re
import sys

# -------------------------------------------------------------------------------

key_path = sys.argv[1]
components = re.search(r"^(\-+[^\-]+\-+)\s+(.+)\s+(\-+[^\-]+\-+)$", sys.argv[2], re.DOTALL)

if components:
    key_prefix = components.group(1)
    key_material = "\n".join(re.split(r"\s+", components.group(2)))
    key_suffix = components.group(3)
else:
    raise Exception(f"Key {key_path} entered is not correct format: {sys.argv[2]}")

with open(key_path, "w") as file:
    file.write(f"{key_prefix}\n{key_material}\n{key_suffix}")
    os.chmod(key_path, 0o664)
