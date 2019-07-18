#!/usr/bin/python
from subprocess import Popen

filename = "pmb.py"
while True:
    print("\nStarting " + filename)
    p = Popen("python " + filename, shell=True)
    p.wait()
