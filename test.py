# coding: utf-8
from crontab import CronTab




cron_tab = CronTab()
#
# job = cron_tab[0]
# cron_tab.new(command='/usr/bin/echo', user='roman')

mode = "every"
if mode == "every":
    project = ""
    spider_name = ""
    command = "curl http://localhost:6800/schedule.json -d project={0} -d spider={1}".format(project, spider_name)
    job = cron_tab.new(command=command)
    job.hour.every(4)

cron_tab.write('ambiencedata_scrapyd.tab')