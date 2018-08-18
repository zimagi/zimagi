#!/usr/bin/env python3

from shared import update_keys

import argparse
import os


def main():
    parser = argparse.ArgumentParser(description='Copy generated SSH keys to the .ssh directory')    
    args = parser.parse_args()
    
    # Copy generated keys to the .ssh directory
    update_keys()


if __name__ == "__main__":
    os.chdir(os.path.abspath(os.path.dirname(__file__) + '/..'))
    main()
