import sys


class Logger(object):
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log = open(filename, "w")

    def write(self, message):
        self.terminal.write(message)   # print to screen
        self.log.write(message)        # write to file

    def flush(self):
        pass
