#!/usr/bin/env python
import sys
import os

npath = os.path.abspath(os.path.dirname(__file__)) + '/term_app/'
os.chdir(npath)
sys.path.append(npath)
import main


if __name__ == '__main__':
    main.main_loop()
