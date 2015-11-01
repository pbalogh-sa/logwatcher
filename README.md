# Logwatcher

[![Build Status](https://travis-ci.org/pbalogh-sa/logwatcher.svg)](https://travis-ci.org/pbalogh-sa/logwatcher)

__Create info, error, alert message when a defined regexp found on logfile.__

### Prerequirements:

python tailer
install:

```
sudo pip install tailer
```

```
  Usage: logwatcher.py [options]

  Options:
    -h, --help  show this help message and exit
    -f FILE     open logfile [default: stdin]
    -p PATTERN  serched pattern [mandatory]
    -l LINE     regex search in number of log lines [default: 1]
    -a ALERT    set alert level [default: print alert message to stdout]
    -t, --tee   print alert message to stdout [defautl: false]
```
