#!/usr/bin/python
# -*- coding: utf-8
#

import argparse
import os
import sys

PROG = os.path.basename(sys.argv[0]).rstrip('.py')
PROG_DESC = 'Send notification for redmine issue due date'


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=PROG_DESC)
    args = parser.parse_args()
    parser.print_help()
