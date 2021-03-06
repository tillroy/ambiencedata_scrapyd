#!/bin/bash
# Author: Roman Peresoliak
# Description: initiate python environment and run pollution crawler
# Place: use it separately from main scrapyd folder


# path to python virt env
ENV_HOME=/home/roman/PycharmProjects/scrapyd_fork

# path to server run script
DAEMON=$ENV_HOME/scrapyd/scrapyd/scripts/scrapyd_run.py

cd $ENV_HOME
source env/bin/activate

# run in a background "&"
exec python $DAEMON &