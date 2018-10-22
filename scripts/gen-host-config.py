#!/usr/bin/env python3

from shared import generate_dev_inventory, load_inventory

import argparse
import os
import re


def get_host_map(inventory):
    host_map = {'definitions': [], 'masters': [], 'nodes': [], 'etcd': [], 'vault': []}
    
    for server in inventory['masters']:
        host = "{}@{}".format(server['user'], server['ip'])
        host_map['definitions'].append({
            'hostname': server['hostname'],
            'ansible_ssh_host': server['ip'],
            'ansible_user': server['user']
        })
        host_map['masters'].append(server['hostname'])
        
        if 'etcd' in server and server['etcd']:
            host_map['etcd'].append(server['hostname'])
            
        if 'vault' in server and server['vault']:
            host_map['vault'].append(server['hostname'])
        
    for server in inventory['nodes']:
        host = "{}@{}".format(server['user'], server['ip'])
        host_map['definitions'].append({
            'hostname': server['hostname'],
            'ansible_ssh_host': server['ip'],
            'ansible_user': server['user']
        })
        host_map['nodes'].append(server['hostname'])
        
        if 'etcd' in server and server['etcd']:
            host_map['etcd'].append(server['hostname'])
        
        if 'vault' in server and server['vault']:
            host_map['vault'].append(server['hostname'])
        
    return host_map


def generate_host_config(inventory):
    host_map = get_host_map(inventory)
    
    host_config = "\n# Kubernetes host definitions\n"    
    for data in host_map['definitions']:
        host_config += "{} ansible_ssh_host={} ansible_user={} ansible_python_interpreter=/usr/bin/python3\n".format(
            data['hostname'],
            data['ansible_ssh_host'],
            data['ansible_user']
        )
    
    host_config += "\n# Kubernetes masters\n[kube-master]\n"
    for hostname in host_map['masters']:
        host_config += "{}\n".format(hostname)
        
    host_config += "\n# Kubernetes nodes\n[kube-node]\n"
    for hostname in host_map['nodes']:
        host_config += "{}\n".format(hostname)
        
    host_config += "\n# ETCD nodes\n[etcd]\n"
    for hostname in host_map['etcd']:
        host_config += "{}\n".format(hostname)
        
    host_config += "\n# Vault nodes\n[vault]\n"
    for hostname in host_map['vault']:
        host_config += "{}\n".format(hostname)
    
    host_config += "\n# Kubernetes groups\n[k8s-cluster:children]\nkube-node\nkube-master\n"
    
    return host_config


def save_host_config(host_config):
    file = open('hosts/hosts.ini', 'w')
    file.write(host_config)
    file.close()


def main():
    parser = argparse.ArgumentParser(description='Generate an Ansible hosts inventory file')
    parser.add_argument('environment', nargs ='?', action = 'store', default = 'dev')
       
    args = parser.parse_args()
    
    generate_dev_inventory()
    inventory = load_inventory(args.environment)    
    
    save_host_config(generate_host_config(inventory))
   

if __name__ == "__main__":
    os.chdir(os.path.abspath(os.path.dirname(__file__) + '/..'))
    main()
