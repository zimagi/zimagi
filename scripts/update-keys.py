#!/usr/bin/env python3

from shared import update_keys

import argparse
import os


def main():
    parser = argparse.ArgumentParser(description='Copy generated SSH keys to the .ssh directory')
    parser.add_argument('environment', nargs ='?', action = 'store', default = 'dev')
       
    args = parser.parse_args()
    
    # Copy generated keys to the .ssh directory
    update_keys(args.environment)


if __name__ == "__main__":
    os.chdir(os.path.abspath(os.path.dirname(os.path.realpath(__file__)) + '/..'))
    main()
