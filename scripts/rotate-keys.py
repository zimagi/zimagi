#!/usr/bin/env python3

from shared import command, load_inventory, update_keys

import argparse
import os


def generate_key(environment):
    ssh_key = 'keys/id_rsa'
    home_ssh_key = "{}/.ssh/id_rsa".format(os.getenv("HOME"))
    
    ssh_prv_key = None
    ssh_pub_key = None
    
    if environment == 'dev':
        with open(home_ssh_key, 'r') as file:
            ssh_prv_key = file.read()
    
        with open("{}.pub".format(home_ssh_key), 'r') as file:
            ssh_pub_key = file.read()
    else:
        info = command("ssh-keygen -y -q -t rsa -b 4096 -N '' -f {}".format(ssh_key))
    
        with open(ssh_key, 'r') as file:
            ssh_prv_key = file.read()
    
        with open("{}.pub".format(ssh_key), 'r') as file:
            ssh_pub_key = file.read()
    
        if info['status'] != 0:
            raise Exception("Error generating SSH key")

    return (ssh_prv_key, ssh_pub_key)


def rotate_keys(inventory, ssh_pub_key):
    home_ssh_key = "{}/.ssh/id_rsa".format(os.getenv("HOME"))
    
    nodes = inventory['masters']
    nodes.extend(inventory['nodes'])
    
    # Overwrite old keypair with new keypair in home .ssh directory
    for server in nodes:
        host = "{}@{}".format(server['user'], server['ip'])
        
        print("Configuring host: {}".format(host))
        info = command('ssh {} "mkdir -p ~/.ssh" && scp {}.pub {}:~/.ssh/authorized_keys'.format(host, home_ssh_key, host))
        
        if info['status'] != 0:
            raise Exception("Error copying SSH key to host {}".format(host))


def main():
    parser = argparse.ArgumentParser(description='Initialize or rotate Kubernetes node SSH keys')
    parser.add_argument('environment', nargs ='?', action = 'store', default = 'dev')
       
    args = parser.parse_args()
    inventory = load_inventory(args.environment)
    
    if args.environment == 'dev':
        # Ensure Vagrant keys are transferred / generated
        update_keys(args.environment)
    
    # Generate new SSH keypair
    ssh_prv_key, ssh_pub_key = generate_key(args.environment)
    
    # Print private key for backup storage
    print(ssh_prv_key)
    print(ssh_pub_key)
        
    # Replace keypairs on all Kubernetes nodes
    rotate_keys(inventory, ssh_pub_key)
    
    # Copy generated keys to the .ssh directory
    update_keys(args.environment)


if __name__ == "__main__":
    os.chdir(os.path.abspath(os.path.dirname(__file__) + '/..'))
    main()
