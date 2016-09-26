#!/usr/bin/env python
from twisted.scripts.twistd import run
from os.path import join, dirname
from sys import argv, path


# FIXME only for local usage
# module_path = "/home/roman/PycharmProjects/scrapyd_fork/scrapyd"
module_path = "/opt/crawler/pollution"
if module_path not in path:
    path.append(module_path)
# FIXME

import scrapyd


def main():
    argv[1:1] = ['-n', '-y', join(dirname(scrapyd.__file__), 'txapp.py')]
    run()

if __name__ == '__main__':
    main()
