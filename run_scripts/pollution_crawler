#!/bin/bash
### BEGIN INIT INFO
# Provides:           pollution_crawler
# Required-Start:     $remote_fs $syslog
# Required-Stop:      $remote_fs $syslog
# Default-Start:      2 3 4 5
# Default-Stop:       0 1 6
# Short-Description:  The pollution_crawler server process
# Description:        server for AmbienceData crawlers
#
### END INIT INFO
#
#  /etc/init.d/pollution_crawler
#
# way to the virt env
SCRAPYD_HOME=/home/roman/PycharmProjects/scrapyd_fork

USER=roman

APPNAME=p_crawler
PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/local/bin
#  full path to the command
DAEMON=/home/roman/PycharmProjects/scrapyd_fork/scrapyd/scrapyd/scripts/scrapyd_run.py
RUN_COMAND=python $DAEMON
#PIDFILE=/var/run/test_scrapyd/pollution_crawler.pid

#LOGFILE=/var/log/$DAEMON.log


. /lib/lsb/init-functions

do_start() {
  #start-stop-daemon --start --pidfile $PIDFILE --user $USER --background --make-pidfile --startas $DAEMON
#  start-stop-daemon -v --start --oknodo --make-pidfile --background --chuid $USER --pidfile $PIDFILE --startas $DAEMON
  #start-stop-daemon -v --start --oknodo --chuid $USER  --background --pidfile $PIDFILE --make-pidfile --start --startas $DAEMON
  start-stop-daemon --start --quiet --chuid $USER:$USER --pidfile $PIDFILE --make-pidfile --startas $DAEMON

  #MSG=$(start-stop-daemon --start -v --user $USER --pidfile $PIDFILE --make-pidfile --background --startas $DAEMON --chuid $USER)

  RETVAL="$?"
  if [ $RETVAL == 0 ]
  then
    log_success_msg "$APPNAME started"    
    log_success_msg $MSG
  fi
}


do_stop() {
  #  need becouse instr below try to sho some msg
  #MSG=$(start-stop-daemon --user $USER --stop --pidfile $PIDFILE)
  RETVAL="$?"
  #log_failure_msg $MSG




  if [ $RETVAL == 0 ]
  then
    #rm -f $PIDFILE

    start-stop-daemon --user $USER --stop --name $APPNAME
    log_success_msg "Stopped"
  else
    log_failure_msg "Not running"
  fi
}

case "$1" in
  start)
    cd $SCRAPYD_HOME
    source env/bin/activate
    # run in a background
    exec python $DAEMON &
  ;;
  stop)
    log_failure_msg "ss"
  ;;
  restart)
    do_stop
    do_start
  ;;
  status)
    status_of_proc -p $PIDFILE $APPNAME && exit 0 || exit $?
  ;;
  *)
    echo "Usage: /etc/init.d/$APPNAME {start|stop|restart|status}"
    exit 1
  ;;
esac

exit 0
