#!/usr/bin/python

import sys, os
import threading
import time

exitFlag = 0

class myThread (threading.Thread):
    def __init__(self, threadID, name, counter, iterations=10):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
        self.iterations = iterations
    def run(self):
        print "Starting " + self.name
        print_time(self.name, self.counter, self.iterations)
        print "Exiting " + self.name

def print_time(threadName, delay, counter):
    while counter:
        if exitFlag:
            threadName.exit()
        time.sleep(0.5)
        print "%s: %s" % (threadName, time.ctime(time.time()))
        counter -= 1

# Create new threads
thread1 = myThread(1, "Thread-1", 1, 5)
thread2 = myThread(2, "Thread-2", 2, 15)

# Start new Threads
thread1.start()
thread2.start()

print "Exiting Main Thread"

while thread2.is_alive():
    time.sleep(3)
    os.system('clear')
    print "awake again [%s]" % thread2.is_alive()

