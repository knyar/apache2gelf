#!/usr/bin/env python
import sys
import re
import graypy
import logging
import atexit
import argparse
from subprocess import Popen, PIPE
from time import sleep
from threading import Thread
from thread import interrupt_main
from Queue import Queue, Empty
from signal import signal, SIGTERM

# Copyright (c) 2012 Anton Tolchanov <me@knyar.net>
# https://github.com/knyar/apache2gelf

parser = argparse.ArgumentParser(description='Watches php error log and delivers messages to graylog2 server via GELF')
parser.add_argument('--localname', dest='localname', default=None, help='local host name (default: `hostname`')
parser.add_argument('--host', dest='host', default='localhost', help='graylog2 server hostname (default: localhost)')
parser.add_argument('--port', dest='port', default='12201', help='graylog2 server port (default: 12201)')
parser.add_argument('--facility', dest='facility', default='php_log', help='logging facility (default: php_log)')
parser.add_argument('--vhost', dest='vhost', help='Add additional "vhost" field to all log records. This can be used to differentiate between virtual hosts.')
parser.add_argument('filepath', help='path to PHP error log file')
args = parser.parse_args()

def enqueue_output(out, queue):
    """Thread function that gets log records from tail process and puts them into the queue"""
    for line in iter(out.readline, b''):
        queue.put(line)
    out.close()

def reap_child(proc):
    """Thread function that exits parent process if its child dies"""
    proc.wait()
    print "Child process killed, exiting"
    interrupt_main()

proc = Popen(['tail', '-n', '0', '-F', args.filepath], stderr=open('/dev/null', 'w'), stdout=PIPE, bufsize=1)
# We should kill child process when master process exits or gets killed
atexit.register(proc.kill)
signal(SIGTERM, lambda signum, stack_frame: exit(1))

queue = Queue()
thread_worker = Thread(target=enqueue_output, args=(proc.stdout, queue))
thread_reaper = Thread(target=reap_child, args=(proc,))
for thread in (thread_worker, thread_reaper):
    thread.daemon = True
    thread.start()

logger = logging.getLogger(args.facility)
logger.setLevel(logging.DEBUG)
logger.addHandler(graypy.GELFHandler(args.host, int(args.port), debugging_fields=False, localname=args.localname))

record = {}
if args.vhost: record['vhost'] = args.vhost

adapter = logging.LoggerAdapter(logging.getLogger(args.facility), record)

def flush_message(message):
    """Flush accumulated multi-line message to graylog2 server"""
    if message != '': adapter.info(message.rstrip())

message = ''
while True:
    try: line = queue.get_nowait()
    except Empty:
        # No lines found, flush message to graylog2 server and sleep
        flush_message(message)
        message = ''
        sleep(1)
        continue
    else:
        # New line found
        matches = re.search('^\[\d\d-...-\d{4} \d\d:\d\d:\d\d\] (.*)', line)
        if matches:
            # So, it's a new message - we should send the previous one and start accumulating a new one
            flush_message(message)
            if args.vhost:
                message = "%s: %s" % (args.vhost, matches.group(1))
            else:
                message = matches.group(1)
        else:
            # Not a new message - so simply add a line to accumulated message
            message += line

