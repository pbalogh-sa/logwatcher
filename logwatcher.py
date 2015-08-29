#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
import time
import errno
import stat
import optparse
import sys
import tailer
import signal
from subprocess import call
from collections import deque
import re

childpid = 0


class terrier():

    def __init__(self, opts):
        self.fexist = False
        self.alert = opts.ALERT
        self.line = opts.LINE
        self.prstdout = opts.STDOUT
        self.prevsize = 0
        if opts.FILE == 'stdin':
            self.stdin = True
        else:
            self.stdin = False
            self.filename = filename_handler(os.path.realpath(opts.FILE))
            try:
                self.file = open(self.filename, 'r')
                self.fexist = True
                self.filestat = os.stat(self.filename)
            except IOError:
                print 'File Not Found: %s' % self.filename
                sys.exit(1)
        self.pattern = opts.PATTERN
        self.que = deque(maxlen=self.line)

    def __del__(self):
        if not self.stdin and self.fexist:
            self.file.close()

    def run(self):
        if self.stdin:
            self.findpattern_from_stdin()
        else:
            self.findpattern_from_file()

    def findpattern_from_file(self):
        if self.line == 1:
            for line in tailer.follow(self.file):
                self.make_alert(line)
        else:
            for line in tailer.follow(self.file):
                self.check_multiline(line)

    def findpattern_from_stdin(self):
        if self.line == 1:
            for line in sys.stdin:
                self.make_alert(line)
        else:
            for line in sys.stdin:
                self.check_multiline(line)

    def make_alert(self, line):
        if self.check_pattern(line):
            self.que.append(line)
            if self.alert != 'stdout':
                call(['urun', self.alert, line])
            if self.prstdout:
                self.print_to_stdout()

    def check_pattern(self, line):
        return re.search(self.pattern, line)

    def check_multiline(self, line):
        self.que.append(line)
        self.mline = "\n".join(list(self.que))
        self.alertmessage = " - ".join(list(self.que))
        if re.findall(self.pattern, self.mline, re.MULTILINE):
            if self.alert != 'stdout':
                call(['urun', self.alert, self.alertmessage])
            if self.prstdout:
                self.print_to_stdout()

    def print_to_stdout(self):
        print '%s on %s: %s' % (self.alert, time.strftime('%Y-%m-%d'), list(self.que))

    def check_file(self):
        if os.path.isfile(self.filename):
            self.inode = os.stat(self.filename)
            if self.inode.st_ino == self.filestat.st_ino:
                if self.inode.st_size >= self.prevsize:
                    self.prevsize = self.inode.st_size
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False


class debugger():

    def __init__(self, opts):
        self.opts = opts

    def dprint(self):
        print self.opts


def signal_handler(signal, frame):
    os.kill(childpid, 3)
    sys.exit(0)


def filename_handler(filename):
    if filename.find('{') >= 0:
        tmp1 = filename.split('{')
        tmp2 = tmp1[1].split('}')
        datestr = tmp2[0].split('-')
        for i in range(0, 3):
            if datestr[i] == 'YYYY' or datestr[i] == 'MM' or datestr[i] == 'DD':
                pass
            else:
                print 'Date Format error in filename. Use YYYY-MM-DD or DD-MM-YYYY etc.!\n'
                sys.exit(-1)

        dateformat = {
            'YYYY': time.strftime('%Y'),
            'MM': time.strftime('%m'),
            'DD': time.strftime('%d')
        }
        currdate = dateformat[datestr[0]] + '-' + dateformat[datestr[1]] + '-' + dateformat[datestr[2]]
        filename = tmp1[0] + currdate + tmp2[1]
    else:
        filename = filename
    return filename


def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    parser = optparse.OptionParser()
    parser.add_option('-f', help='open logfile [default: stdin]', dest='FILE', default='stdin')
    parser.add_option('-p', help='serched pattern [mandatory]', dest='PATTERN')
    parser.add_option('-l', type=int, help='regex search in number of log lines [default: 1]', dest='LINE', default=1)
    parser.add_option('-a', help='set alert level [default: print alert message to stdout]', dest='ALERT', default='stdout')
    parser.add_option('-t', '--tee', action='store_true', help='print alert message to stdout [defautl: false]', dest='STDOUT', default=False)
    (opts, args) = parser.parse_args()

    if opts.ALERT == 'stdout':
        opts.STDOUT = True
    else:
        if opts.ALERT == 'info' or opts.ALERT == 'error' or opts.ALERT == 'alert':
            pass
        else:
            parser.print_help()
            print 'Valid alert type missing: [info, error, alert]'
            sys.exit(-1)

    mandatories = ['PATTERN']
    for m in mandatories:
        if not opts.__dict__[m]:
            print "mandatory option is missing\n"
            parser.print_help()
            sys.exit(-1)

#    d = debugger(opts)
#    d.dprint()

    w = terrier(opts)
    filetailer = os.fork()
    if filetailer == 0:
        childpid = os.getpid()
        w.run()
    while True:
        if w.check_file():
            pass
        else:
            print 'Logfile removed!'
            os.kill(filetailer, 3)
            sys.exit(1)
        time.sleep(5)

if __name__ == '__main__':
    main()
