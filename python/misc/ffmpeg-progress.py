
import pexpect, os, re
from time import time as now

def progress(percent=0.0, bar="|", bg=":"):
    length = 80.0 # number of ASCII chars
    width = int((float(percent)/100.0) * length)+1
    return (bar*width).ljust(int(length), bg)

def elapsed():
    global time_start
    return now() - time_start

def banner(percent_current, frame_number):

    frame_number = float(frame_number)

    os.system('clear')

    print "THIS STATUS BAR: %s" % (percent_current)
    print "%s  %2d%%" % (progress(percent_current/4, '_', ' '), percent_current/4)
    print "%s  %2d%%" % (progress(percent_current, '|', ':'), percent_current)

    return;


def timecode_value(tc):
    print "timecode_value", tc
    hours, minutes, seconds = tc.split(":")
    return float(seconds) + (float(minutes) * 60) + (float(hours) * 60 * 60)



i = 0
line = ''
duration_total = 0
file_name = 'example.mov'
cmd = 'ffmpeg -i ' + file_name + ' -strict -2 -c:a copy -c:v prores_ks -profile:v 0 -qscale:v 19 -s 1920x1080 -threads 0 -hide_banner -y  trash.mov'
thread = pexpect.spawn(cmd)
cpl = thread.compile_pattern_list([
    pexpect.EOF,
    "^(frame=.*)"
])

time_start = now()
current_frame = 0
duration_total = 0
# os.system('clear')


# grab the header meta data
# iterate to find Duration
while (not re.compile('^Press').match(line)):
    i = i + 1
    line = thread.readline().strip()
    if (re.compile('^Duration').match(line)):
        duration_total = timecode_value(line.split(',')[0].split(' ')[1])


while True:
    i = thread.expect_list(cpl, timeout=None)
    if i == 0: # EOF
        print "the sub process exited"
        break
    elif i == 1:
        try:
            print "!", tuple(re.sub('=\s+', '=', thread.match.group(0).strip()).split(' '))
            array = tuple(re.sub('=\s+', '=', thread.match.group(0).strip()).split(' '))
            frame = array[0]
            fps = array[1]
            q = array[2]
            size = array[3]
            time = array[4]
            brate = array[5]
            f, n = tuple(frame.split('='))
            tc, ts = tuple(time.split('='))
            fps_value = float(tuple(fps.split('='))[1])
            current_frame = float(n)
            current_time = timecode_value(ts)
            percentage = (current_time / duration_total * 100) # eg. 23.05
            banner(percentage, n)
            # 1% = current_time/percentage
            total_time = (current_time/percentage)*100
            est_duration = (total_time * duration_total)/10
            padding = (est_duration* 0.22)

            print "Estimate: %3d seconds (%s)" % (est_duration + padding, fps)

            # print "%s %2d%%" % (n, (timecode_value(ts) / duration_total * 100))
        except:
            print ""

        thread.close

    elif i == 2:
        #unknown_line = thread.match.group(0)
        #print unknown_line
        pass

print elapsed()