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

APPNAME=scrapyd_run
PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/local/bin
#  full path to the command
DAEMON=$SCRAPYD_HOME/scrapyd/scrapyd/scripts/scrapyd_run.py

#PIDFILE=/var/run/pollution_crawler.pid
PIDFILE=/home/roman/PycharmProjects/scrapyd_fork/scrapyd/scrapyd/scripts/pollution_crawler.pid

#LOGFILE=/var/log/$DAEMON.log


. /lib/lsb/init-functions

do_start() {
    #start-stop-daemon --start --quiet --chuid $USER:$USER --pidfile $PIDFILE --make-pidfile --startas $DAEMON
    # it works under root
    start-stop-daemon --start --quiet --pidfile $PIDFILE --background --make-pidfile --startas $DAEMON

    MSG=$(start-stop-daemon --start --quiet --pidfile $PIDFILE --background --make-pidfile --startas $DAEMON --user roman)
    log_success_msg $MSG

    #start-stop-daemon --chuid $USER:$USER --start --name $APPNAME --quiet --background --startas $DAEMON -v
    RETVAL="$?"
    if [ $RETVAL == 0 ]
    then
        log_success_msg "$APPNAME started"
    fi
}

do_stop() {
  #  need becouse instr below try to sho some msg
  MSG=$(start-stop-daemon --stop --pidfile $PIDFILE)
  RETVAL="$?"

  if [ $RETVAL == 0 ]
  then
    rm -f $PIDFILE
    log_success_msg "Stopped"
  else
    log_failure_msg "Not running"
  fi
}

case "$1" in
  start)
    cd $SCRAPYD_HOME
    source env/bin/activate
    do_start
  ;;
  stop)
    do_stop
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