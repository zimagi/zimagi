
from pathlib import Path

import os
import yaml
import stat
import subprocess
import shutil


ssh_key = "keys/id_rsa"


def load_inventory():
    inventory = None
    
    with open("inventory.yml", 'r') as stream:
        try:
            inventory = yaml.load(stream)

        except yaml.YAMLError as error:
            print(error)
            
    return inventory


def update_keys():
    home = str(Path.home())
    home_ssh_key = "{}/.ssh/id_rsa".format(home)
    home_ssh_pub_key = "{}/.ssh/id_rsa.pub".format(home)
    
    shutil.copyfile(ssh_key, home_ssh_key)
    os.chmod(home_ssh_key, stat.S_IRUSR | stat.S_IWUSR)
    
    shutil.copyfile("{}.pub".format(ssh_key), home_ssh_pub_key)


def command(command_str, stdin=None):
    process = subprocess.Popen(command_str,
                               shell=True,
                               stdin=stdin,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    
    stdoutdata, stderrdata = process.communicate()
        
    return {
        'stdout': stdoutdata, 
        'stderr': stderrdata, 
        'status': process.returncode
    }
