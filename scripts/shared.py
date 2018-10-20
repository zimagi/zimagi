
from pathlib import Path

import os
import yaml
import stat
import subprocess
import shutil


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


def generate_dev_inventory():
    inventory_file = "inventory.dev.yml"
    inventory = {"masters": [], "nodes": []}
    
    if os.path.isfile("vagrant/config.yml"):
        vagrant_config_file = "vagrant/config.yml"
    else:
        vagrant_config_file = "vagrant/default.config.yml"
    
    istream = open(vagrant_config_file, 'r')
    config = yaml.load(istream)
    istream.close()
    
    for index in range(1, config["masters"] + 1):
        inventory["masters"].append({
            "ip": config["master_{}_ip".format(index)],
            "hostname": config["master_{}_hostname".format(index)],
            "os": config["os"],
            "user": config["user"],
            "etcd": config["master_{}_etcd".format(index)]
        })
        
    for index in range(1, config["nodes"] + 1):
        inventory["nodes"].append({
            "ip": config["node_{}_ip".format(index)],
            "hostname": config["node_{}_hostname".format(index)],
            "os": config["os"],
            "user": config["user"],
            "etcd": config["node_{}_etcd".format(index)]
        })
        
    ostream = open(inventory_file, 'w')
    yaml.dump(inventory, ostream, default_flow_style=False)
    ostream.close()


def load_inventory(environment):
    inventory = None
    
    with open("inventory.{}.yml".format(environment), 'r') as stream:
        try:
            inventory = yaml.load(stream)

        except yaml.YAMLError as error:
            print(error)
            
    return inventory


def update_keys(environment):
    home = str(Path.home())
    home_ssh_key = "{}/.ssh/id_rsa".format(home)
    home_ssh_pub_key = "{}/.ssh/id_rsa.pub".format(home)
        
    if environment == "dev":
        ssh_key = "vagrant/private_key"
        info = command("ssh-keygen -y -f {}".format(ssh_key))
        
        if info['status'] != 0:
            raise Exception("Error reading SSH key from Vagrant {}".format(ssh_key))
        
        ostream = open(home_ssh_pub_key, "w")
        ostream.write(info['stdout'].decode("utf-8"))
        ostream.close()
    else:
        ssh_key = "keys/id_rsa"
    
    shutil.copyfile(ssh_key, home_ssh_key)
    os.chmod(home_ssh_key, stat.S_IRUSR | stat.S_IWUSR)
    
    if environment != "dev":
        shutil.copyfile("keys/id_rsa.pub".format(ssh_key), home_ssh_pub_key)
