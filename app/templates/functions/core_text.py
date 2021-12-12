import re

#
# Text processing functions
#

def split_text(text, pattern):
    return re.split(pattern, text)
