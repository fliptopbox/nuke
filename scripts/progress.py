import subprocess
import re
import time
import sys, os

file_name = 'example.mov'
cmd = 'ffmpeg -i ' + file_name + ' -strict -2 -c:a copy -c:v prores_ks -profile:v 0 -qscale:v 19 -s 1920x1080 -threads 0 -hide_banner -y  trash.mov'

process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,bufsize=1, universal_newlines=True)



post_padd = ''
initial_padd = '\n\n'
media_time = None
media_duration = None
re_progress = re.compile('^frame')

def tc_seconds(tc='00:01:23.45'):
    i = 0
    total = 0
    array = reversed(tc.split(':'))
    for part in array:
        value = float(part)
        total += max((pow(60,i), 1)) * value
        i += 1
    return total

# Poll process for new output until finished
while True:
    nextline = process.stdout.readline().rstrip()
    if process.poll() is not None:
        break

    if re.match(re_progress, nextline):
        # banner()
        # sys.stdout.write('\x1b[2K')
        if initial_padd:
            print initial_padd
            initial_padd = None

        media_time = re.compile('.*time=([0-9\:\.]+).*', re.I).match(nextline)
        if media_duration and media_time:
            media_time = tc_seconds(media_time.group(1))

            pcent = int(media_time/media_duration*100)+1
            pcent = min(pcent, 100)

            sys.stdout.write('\x1b[1A')
            print("progress %s %s%%" % (('|'*pcent).ljust(100, ':'), pcent))
            print "%s\r" % (nextline),
            # sys.stdout.write('\x1b[1A')

        post_padd = "\n\n"
        continue

    tmp = re.compile('\s+duration\: ([0-9\:\.]+).*', re.I).match(nextline)
    if tmp and not media_duration:
        media_duration = float(tmp.group(1).replace(':',''))

    print post_padd, nextline

    #sys.stdout.write(nextline)
    sys.stdout.flush()

output = process.communicate()[0]
exitCode = process.returncode

if (exitCode == 0):
    print "done"
else:
    raise ProcessException(cmd, exitCode, output)