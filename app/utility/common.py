from inspect import getframeinfo, stack
from django.conf import settings

import binascii
import os
import psutil
import sys
import logging
import traceback


def config_value(name, default=None):
    # Order of precedence
    # 2. Local environment variable if it exists
    # 3. Default value provided

    value = default
    
    # Check for an existing environment variable
    try:
        value = os.environ[name]
    except:
        pass
    
    return value


def generate_token():
    return binascii.hexlify(os.urandom(20)).decode()


def flatten(source_list):
    flattened_list = []
    
    for item in source_list:
        if isinstance(item, list):
            flattened_list.extend(flatten(item))
        else:
            flattened_list.append(item)
            
    return flattened_list


def system_logger():
    return logging.getLogger('django')


def display_error(info, logger=None):
    if not logger:
        logger = system_logger()
    
    logger.debug("MAJOR ERROR -- PROCESS ENDING EXCEPTION -- {}".format(info))
    traceback.print_tb(sys.exc_info()[2])
    

def memory_in_mb(mem):
    #documentation on memory fields: http://psutil.readthedocs.io/en/latest/#id1
    unit = 1024 * 1024 # MB
    return {
        'total': mem.total / unit,
        'available': mem.available / unit, #*
        'used': mem.used / unit, #*
        'free': mem.free / unit,
        'active': mem.active / unit,
        'inactive': mem.inactive / unit,
        'buffers': mem.buffers / unit,
        'cached': mem.cached / unit,
        'shared': mem.shared / unit,
    }

def print_memory(message = "Max Memory"):
    caller = getframeinfo(stack()[1][0])
    mem = memory_in_mb(psutil.virtual_memory())   
    
    
    print("{}/{} | {}: {:.2f}MB {:.2f}MB".format(caller.filename, caller.lineno, message, mem['available'], mem['used']))

def csv_memory(message = "Memory"):
    caller = getframeinfo(stack()[1][0])
    mem = memory_in_mb(psutil.virtual_memory())
    
    return('"{}","{}",{:.4f},{:.4f},{:.4f},{:.4f},{:.4f},{:.4f},{:.4f},{:.4f},{:.4f}'.format(caller.filename, message, mem['total'], mem['available'], mem['used'], mem['free'], mem['active'], mem['inactive'], mem['buffers'], mem['cached'], mem['shared']))