import os, sys, re, subprocess, time, datetime, json, argparse, socket, base64
import SimpleHTTPServer, SocketServer
import tempfile, shutil

from distutils.spawn import find_executable
from string import Template

def version ():
    major = 0
    minor = 4
    build = 45
    ver = [str(major), str(minor), str(build)]
    return '.'.join(ver)


def banner():
    print "\nM A K E - P R O X Y (version:%s)\n\n" % version()


def pipe_path(path):
    path = path.strip()
    return re.sub('[\\\/]', '|', path)

def strip_trailing_slash(path=''):
    if not path: return ''
    return re.sub('[\\\/]+$', '', path)

def create_web_monitor(dst):
    dct = [
        ('index.html', "{{index.html}}"),
        ('style.css', "{{style.css}}"),
        ('zepto.min.js', "{{zepto.min.js}}"),
        ('main.js', '{{main.js}}')
    ]
    output = dst + get_prefix()
    for asset in dct:
        # unpack and write the asset to the asset folder
        filename, b64string = (asset)
        b64string = base64.b64decode(b64string)
        open(output + filename, 'w').write(b64string)

    os.chdir(output)
    PORT = 8000
    attempt = 0

    while (attempt < 5):
        try:
            Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
            httpd = SocketServer.TCPServer(("", PORT), Handler)
            print "serving at port", PORT
            httpd.serve_forever()
        except:
            attempt += 1
            print "Waiting for server ...", attempt
            time.sleep(5)

def halt(i=0):
    sys.exit(i)

def cls(n=None):
    # os specific "clear"
    # or line feeds
    method = 'cls' if os.name == 'nt' else 'clear'
    if n == None or n < 1:
        os.system(method)
        banner()
        return
    print "\n"*n

def slash():
    delim = "\\" if os.name == 'nt' else "/"
    return delim

def folder_fix(path, char=None):
    # if char == None: char = slash()
    # if char == '\\': char += char #regex escape "\"
    char = "|"
    path = path.replace(r'[\r]', '').strip()
    fix_path = path or ''
    fix_path = fix_path.replace('\\', char)
    fix_path = fix_path.replace('/', char)

    fix_path = fix_path.replace('||', '|')
    fix_path = fix_path.replace('|', slash())


    return fix_path

def tsv(type='NONE', desc="No description", value=" ", extra=" "):
    who = config('worker') or 'UNKOWN'
    ts = now()
    return '\t'.join([type.ljust(8), who, str(desc), str(value), (extra), ts])

def sizeof_fmt(num, suffix='B'):
    for unit in ['','K','M','G','T','P','E','Z']:
        if abs(num) < 1024.0:
            return "%3.2f %s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)

def now(style='%Y/%m/%d %H:%M:%S'):
    if style == 'epoc':
        # javascript uses millisecons 13 characters
        ts = time.time()
        return str(int(round(time.time() * 1000)))
    if style == 'time': style = '%H:%M:%S'
    if style == 'microsecond': style = '%H:%M:%S.%f'
    if style == 'filename': style = '%Y%m%d_%H%M%S'
    return str(datetime.datetime.now().strftime(style))

def tc_seconds(tc='00:00:00.00'):
    i = 0
    total = 0
    array = reversed(tc.split(':'))
    for part in array:
        value = float(part)
        total += max((pow(60,i), 1)) * value
        i += 1
    return total


# the FFMPEG parameters
def get_ffmpeg_command(input_filename, output_filename):
    global which_ffmpeg

    command = []
    command += ['"%s"' % which_ffmpeg]
    command += ['-i', '"%s"' % input_filename]
    command += ['-strict', '-2']
    command += ['-c:a', 'copy']
    command += ['-c:v', config('prores_encoder')]
    command += ['-profile:v', str(config('prores_profile'))]
    command += ['-qscale:v', str(config('prores_quality'))]

    if config('dimensions') != 'none':
        command += ['-s', config('dimensions')]

    command += ['-threads', 'none', '-hide_banner', '-y']
    # command += ['-progress', 'http://localhost:8000/bruce/'] ## cause web server error on POST
    command += ['-metadata comment="ORIGINAL: %s"' % (input_filename)]
    command += ['"%s.part.mov"' % output_filename]
    return ' '.join(command)

def get_bash_script(input_relative, output_relative):

    bash_string = [
        input_relative,
        output_relative
    ]

    return '\n'.join(bash_string)

def get_ignored_folders():
    global ignore_file_name
    folder = str(config('dst'))
    file_name = "%s%s%s" % (folder, slash(), ignore_file_name)

    lines = []
    try:
        file = open(file_name, 'r')
        append_to_log(tsv("INFO", "Ignore file found", file_name))

    except:
        append_to_log(tsv("INFO", "Nothing to ignore", file_name))
        return lines

    # return array of folders to ignore
    for line in file:
        line = line.strip()
        clean_path = pipe_path(line).replace('|', '\t')
        lines.append([re.compile('^'+clean_path), line])

    return lines

previous_rex = None
def ignore_folder(path):
    global ignore_folders
    global previous_rex

    path = path.strip()
    rel_path = path.replace(config('dst'), '') # relative path
    rel_path = pipe_path(rel_path).strip().replace('|', '\t')

    if previous_rex and previous_rex.match(rel_path):
        return True;

    for rex, text in ignore_folders:
        match = rex.match(rel_path)
        if match:
            previous_rex = rex
            msg = tsv("IGNORE", "Ignore base folder", text)
            append_to_log(msg)
            break


    # halt()
    return match

def create_meta_data():

    global file_count
    global total_bytes
    global ignore_folders

    source = str(config('src'))
    destination = str(config('dst'))
    file_count = 0

    print "ignore_folders", ignore_folders

    for root, subdirs, files in os.walk(source):
        for file in files:

            # skip dot files (eg ._myVideoFile.MOV)
            if re.compile("^\.").match(file):
                continue


            file = re.sub('\r', '', file)

            input_filename = "%s%s%s" % (root, slash(), file)
            input_extension = re.search('([a-z0-9]+)$', input_filename, re.IGNORECASE).group(0)
            input_file_size = os.path.getsize(input_filename)

            if ignore_folder(input_filename):
                continue

            base =  input_filename.replace(source, "")
            input_folder = base

            output_folder = ("%s%s" % (destination, base)).replace(file, '')
            output_extension = re.compile('mov', re.IGNORECASE).match(input_extension) and input_extension or 'mov'
            output_filename = output_folder + re.sub('([^\.]{2,})$', output_extension, file)

            base_folder = "%s" % (output_folder.replace(destination, ''))


            output_filename = folder_fix(output_filename)
            output_folder = folder_fix(output_folder)

            input_filename = folder_fix(input_filename)
            input_folder = folder_fix(input_folder)

            input_rel = input_filename.replace(source, "")
            output_rel = output_filename.replace(destination, "")

            # skip non-video media
            if not is_video.match(file):
                continue

            # skip ignored folders
            if (ignore_folder(base_folder)):
                continue

            # skip large files
            byte_limit = config('byte_limit')
            if (byte_limit > 0) and (input_file_size > byte_limit):
                msg = tsv("WARN", "Size limit exceeded", base + ' ' + sizeof_fmt(input_file_size), sizeof_fmt(byte_limit))
                errors.append(msg)
                append_to_log(msg)
                continue

            # skip existing transcoded files
            if skip_existing_files and os.path.isfile(output_filename):
                msg = tsv("SKIP", "Output media exists", output_filename)
                errors.append(msg)
                append_to_log(msg)
                continue

            # is this a transcode (ie input does not match output)
            if input_extension.lower() != output_extension.lower():
                if config('transcode') == 'none':
                    msg = tsv("SKIP", "Do not transcode", input_filename , "%s to %s" % (input_extension,output_extension))
                    errors.append(msg)
                    append_to_log(msg)
                    continue

                msg = tsv("TRANS", "Transcode media", input_filename , "%s to %s" % (input_extension,output_extension))
                errors.append(msg)
                append_to_log(msg)


            # create destination output folder(s)
            if not os.path.isdir(output_folder):
                # print "Create folder:", output_folder
                try:
                    os.makedirs(output_folder)
                except:
                    msg = tsv("ERROR", "Can't create folder", output_folder)
                    if not errors.count(msg):
                        errors.append(msg)
                        append_to_log(msg)
                    continue

            # create the ffmpeg command file, if the output media does not exist
            if os.path.isdir(output_folder) and not os.path.isfile(output_filename):
                # print "Create bash file: %s.ffmpeg" % (output_filename)
                # ensure previous meta data files are removed
                meta_filename = "%s.ffmpeg" % (output_filename)

                if os.path.isfile(meta_filename+'.locked'):
                    append_to_log(tsv("REMOVE", "Removed meta data lock file", meta_filename), True)
                    os.remove(meta_filename)

                try:
                    bash_file = open(meta_filename, 'w')

                except:
                    # errors.append("Can't create file (%s.ffmpeg)" % (output_filename))
                    msg = tsv("ERROR", "Can't create command file", "%s.ffmpeg" % (output_filename))
                    errors.append(msg)
                    append_to_log(msg)
                    continue

                # create the ffmpeg metadata file
                bash_string = get_bash_script(input_rel, output_rel)
                bash_file.write(bash_string)
                bash_file.close()

                file_count += 1
                total_bytes += input_file_size
                new_row = [bash_string, input_filename, output_filename]
                stack.append(new_row)

                append_to_log(tsv("ADDED", "Added media file", input_filename, sizeof_fmt(input_file_size)))

    append_to_log(tsv("INFO", "File count", file_count))
    append_to_log(tsv("INFO", "Total bytes", sizeof_fmt(total_bytes)))

    config('total_files', file_count)
    config('total_bytes', total_bytes)
    update_progress(0)

    return


def append_to_log(text, echo=False):
    global log_file_name
    destination = config('dst')
    filename = get_prefix(log_file_name)
    log_file = open("%s/%s" % (destination, filename), 'ab+')
    log_file.write(text+'\n')
    log_file.close()
    if echo:
        print text

def present_warnings():
    if len(errors):
        cls(3)
        print "-------------------------------------------"
        print " WARNINGS that occured while preparing"
        print "-------------------------------------------"
        print "\n - " + ('\n - '.join(errors))
        cls(3)
    return

def get_next_task():
    # returns a FFMPEG metadata file
    destination = str(config('dst'))
    work = []

    for root, subdirs, files in os.walk(destination):
        for file in files:
            filename = "%s%s%s" % (root, slash(), file)
            if ignore_folder(filename):
                continue

            if os.path.isfile(file+'.locked'):
                print "ALERT media lock file already exists for", file
                continue

            if re.search('ffmpeg$', file):

                work.append(filename)
                get_progress()
                break
        if len(work): break

    if len(work):
        return work[0]

    return None

def encode_type(ifp='', ofp=''):
    ext = re.compile('.*\.([0-9a-z]+)$', re.IGNORECASE)
    print "encode_type (%s) (%s)" % (re.match(ext, ifp).group(1), re.match(ext, ofp).group(1))
    ifp = re.match(ext, ifp).group(1) or ''
    ofp = re.match(ext, ofp).group(1) or ''
    return "%s to %s" % (ifp.upper(), ofp.upper())

def transcode_footage():
    global which_ffmpeg

    src = config('src')
    dst =  config('dst')
    task_filename = get_next_task()

    append_to_log(tsv('WORKER', 'Worker joined ... ', config('worker_addr')))
    while task_filename:

        base_filename = re.sub('.ffmpeg$', '', task_filename)
        base_filename = re.sub(dst, '', base_filename)

        src_filename = src + base_filename
        dst_filename = dst + base_filename

        print "%s: (%s) %s" % (config('worker'), config('worker_addr'), task_filename)

        try:
            os.rename(task_filename, task_filename+'.locked')
        except:
            print "File exists %s %s" % (task_filename, task_filename+'.locked')
            task_filename = get_next_task()


        cls(3)
        work_time = now('time')
        work_worker = config('worker')

        # open the task file and extract src, dest and
        # add create the relative paths for the batch command
        try:
            task_file = open(task_filename+'.locked', 'r').read()
            open(task_filename+'.locked', 'w').write(task_file + '\n' + config('worker') +  ':' + config('worker_addr'))
        except:
            print "Can't open file", task_filename
            task_filename = get_next_task()

        task_file = task_file.split('\n')

        abs_input = folder_fix(src + slash() + task_file[0])
        abs_output = folder_fix(dst + slash() + task_file[1])
        input_size = os.path.getsize(abs_input)

        tmp_folder = tempfile.mkdtemp(prefix='ffmpeg_')
        tmp_filename = folder_fix(tmp_folder + slash() + 'temp.mov')


        print "\n\nSRC: %s\nDST: %s\n" % (abs_input, tmp_filename)

        media_encode = encode_type(abs_input, abs_output)
        task_transcode = '' if (task_file[0].lower() == task_file[1].lower) else ' TRANSCODE '


        # task_cmd =  get_ffmpeg_command(abs_input, abs_output)
        task_cmd =  get_ffmpeg_command(abs_input, tmp_filename)

        # print "Executing %d of %d (%d%%)\n\n" % (i, n, int((float(i-1)/float(n)) * 100))
        append_to_log(tsv('WORK', 'Start transcoding', task_filename, "%s (%s)" % (sizeof_fmt(input_size), media_encode)))

        # process = subprocess.call(task_cmd, shell=True)
        process = subprocess.Popen(task_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,bufsize=1, universal_newlines=True)


        post_padd = ''
        initial_padd = '\n\n'
        media_time = 0
        media_duration = 0
        re_progress = re.compile('^frame')

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
                media_duration = tc_seconds(tmp.group(1))

            print post_padd, nextline

            #sys.stdout.write(nextline)
            sys.stdout.flush()

        proc_exitoutput = process.communicate()[0]
        proc_exit = process.returncode


        if proc_exit is not 0:
            print "Exit suprocess error", proc_exitoutput
            msg = tsv("FAIL", "FFMPEG Failed to transcode media", abs_input)
            append_to_log(msg, True)

        # clean-up: rename temp file
        if proc_exit == 0 and os.path.isfile(tmp_filename + '.part.mov'):
            # remove existing files before rename
            if os.path.isfile(abs_output):
                os.remove(abs_output)

            #os.rename(abs_output + '.part.mov', abs_output)
            print "Move complete transcode to destination ..."
            shutil.move(tmp_filename + '.part.mov', abs_output)
            shutil.rmtree(tmp_folder)

            output_size = os.path.getsize(abs_output)
            ratio = float(output_size)/float(input_size)
            report = 'DEFALTE' if ratio else 'INFLATE'
            append_to_log(tsv('WORK', 'Finished transcoding', task_filename, "%s %s %2.2f" % (sizeof_fmt(output_size), report, ratio)))
            update_progress()
            status = 'SUCCESS'
            snooze = 5

            # delete ffmpeg command file IF transcode was successful
            if os.path.isfile(abs_output +'.ffmpeg.locked'):
                os.remove(abs_output + '.ffmpeg.locked')

        else:
            msg = tsv("FAIL", "Failed to create output media", abs_output)
            status = 'ERROR'
            append_to_log(msg, True)
            snooze = 5

        # loop to next file ... or exit
        # print "finished .. zzzzzzz"
        # time.sleep(20)
        print "\n\n%s: Safe to quit. Snoozing for %s seconds" % (status, snooze)
        time.sleep(snooze)
        task_filename = get_next_task()

    append_to_log(tsv('WORKER', 'Worker left ... all done', config('worker'), now()))

def summary_report():
    # generates a summary of stalled transcodes
    # or files imcomplete partials unsaved
    global file_count
    cls(3)
    print "No more work to do ... generating summary report"

    # find all files (*.locked *.part.mov *.ffmpeg)
    extension = re.compile('^.*(locked|part\.mov)$', re.I)

    count = 0
    file_array = []

    # traverse the output folder
    output = config('dst')
    for root, subdirs, files in os.walk(output):
        for file in files:
            if extension.match(file):
                count += 1
                filename = "%s%s%s" % (root, slash(), file)
                file_array.append(filename)
                print "%s) %s %s" % (str(count).rjust(6), root, file)

    print "\n\nWe found %s stagnent files." % str(count)
    print "Would you like to reset and re-process these files?"
    contd = raw_input("Reset and re=process (y/N): ")
    if contd == 'y':
        count = 0
        for row in file_array:

            # always double check incase another node
            # was still working when the list was made
            if not os.path.isfile(row):
                continue

            if re.compile('.*(locked)$', re.I).match(row):
                # rename locked file
                unlocked = re.sub('\.locked$', '', row)
                print "rename %s, %s" % (row, unlocked)

                if os.path.isfile(unlocked):
                    os.remove(unlocked)
                    msg = tsv("REMOVE", "Deleted locked file", unlocked)
                    append_to_log(msg)
                    print msg

                if os.path.isfile(row):
                    os.remove(row)
                    msg = tsv("REMOVE", "Deleted un-locked file", row)
                    append_to_log(msg)
                    print msg

            count += 1

        msg = tsv("RESTART", "Restart transcoding", count)
        append_to_log(msg)
        create_meta_data()
        transcode_footage()
        halt()

def config(key, value=None):
    global config_dct
    # returns config value
    if value != None:
        config_dct[key] = value

    value = config_dct[key]

    if type(value) is unicode:
        value = value.encode('ascii')

    return value


def update_progress(value=1):
    # update config dictionary
    # open existing config
    global destination
    global config_filename

    config_path = "%s%s%s" % (destination, slash(), config_filename)
    config_json = json.loads(open(config_path, 'r').read())

    total_progress = config_json['total_progress']
    total_progress += int(value) or 0
    config('total_progress', total_progress)

    config_json['total_progress'] = total_progress
    config_json['total_files'] = config('total_files')
    config_json['total_bytes'] = config('total_bytes')
    config_json['node_'+config('worker')] = config('worker_addr') + '@' + now('epoc')


    config_file = open(config_path, 'w')
    config_file.write(json.dumps(config_json, indent=4))
    config_file.close()

def get_progress(summary=False):
    diff = min(100.0, (float(config('total_progress')) / float(config('total_files')))* 100)
    cls()
    print "%s  %2.1f%% (%sof%s)" % (('|'*int(diff)).ljust(int(diff)).ljust(100, ':'), diff,config('total_progress'), config('total_files'))


def get_input(msg='User input message', typeis='string', values=[], read_only=False):
    input_msg = (msg.ljust(60, '.') + '(%s): ') % (values[0])
    if read_only == True:
        print "%s" % input_msg
        return values[0]

    input_value = str(raw_input(input_msg or ''))
    def get_string(val):
        if input_value == '': return str(values[0])
        if input_value in values: return input_value
        print "Invalid option. (\"%s\")" % ('", "'.join(values))
        return get_input(msg, typeis, values)

    def get_number(val):
        if input_value == '': return values[0]
        temp_value = int(input_value) or -1
        if temp_value >= values[1] and temp_value <= values[2]: return int(temp_value)
        print "Invalid option. min: %s max: %s" % (values[1], values[2])
        return get_input(msg, typeis, values)

    def get_resize(val):
        if input_value == '': return values[0]
        temp_value = str(input_value)
        if re.compile('^[0-9]{2,4}x[0-9]{2,4}$').match(temp_value): return str(temp_value)
        if re.compile('^no.*$').match(temp_value): return 'none'
        print "Invalid option. \"no\" or (WIDTH)x(HEIGHT) eg: %s" % (values[1:])
        return get_input(msg, typeis, values)

    def get_array(val):
        if input_value == '': return values[0]
        temp_value = str(input_value).lower().strip()
        if re.compile('^(no|none)$').match(temp_value): return 'none'
        if re.compile('^(all)$').match(temp_value): return 'all'
        # TODO: validate know video extensions
        return str(temp_value)

    switch = {
        'string': get_string,
        'number': get_number,
        'dimension': get_resize,
        'array': get_array,
    }

    return switch[typeis](input_value)

def get_prefix(filename=''):
    prefix = ".mkproxy"
    return "%s%s%s" % (prefix, slash(), filename)

if __name__ == "__main__":

    cls()


    parser = argparse.ArgumentParser()
    parser.add_argument("-i", type=str, help="(String) Source folder to scan for video assets")
    parser.add_argument("-o", type=str, help="(String) Destination folder for the transcoded media")
    parser.add_argument("-d", action="store_true", help="Delete and re-create the config file.")
    parser.add_argument("-n", type=str, help="Name the worker, used in the event log")
    parser.add_argument("-w", action="store_true", help="Create a webserver monitor")
    parser.add_argument("-r", action="store_true", help="Refresh metadata files")

    args = parser.parse_args()

    cwd = os.getcwd()
    source = args.i or None
    destination = args.o or None
    worker_id = args.n or str("worker_" + now('filename'))
    worker_addr = socket.gethostbyname(socket.gethostname())
    delete_config_file = args.d
    create_web_assets = args.w
    refresh_metadata = args.r

    # global variables
    # the most common video extensions to match and convert
    is_video = re.compile('.*(mp4|mov|qt|avi|wmv|m4v|mpeg|3gp|mxf|mkv)$', re.IGNORECASE)
    which_ffmpeg = find_executable("ffmpeg")
    gigabyte = 1024.0**3.0
    stack = [] # the FFMPEG execution stack
    errors = [] # the collated runtime errors
    info = [] # the information feedback log file
    file_count = 0
    total_bytes = 0
    skip_existing_files = True
    create_ffmpeg_files = False
    ignore_file_name = get_prefix("ignore.txt")
    ignore_folders = None
    config_filename = get_prefix("config.json")
    config_dct = {
        "src": source,
        "dst": destination,
        "prores_encoder": 'prores_ks',  # 'prores' 'prores_ks' (supports 4444) 'prores_aw'
        "prores_profile": "0", # 0:Proxy, 1:LT, 2:SQ and 3:HQ
        "prores_quality": "22", # huge file: [0 |||||| 9-13 |||||||| 32] terrible quality
        "dimensions": '1920x1080',
        "gig_limit": 20,
        "byte_limit": None,
        "total_files": 0,
        "total_bytes": 0.0,
        "transcode": 'all',
        "total_progress": 0,
        "worker": worker_id,
        "worker_addr": worker_addr,
        "log_filename": "event_log_%s.csv" % (now('filename')),
        "date_created": now(),
        "version": version(),
    }

    # always check the src & dst volumes exist
    while source == None or not os.path.isdir(source):
        print "Source folder does not exist!"
        source = raw_input("Source folder(%s): " % (source)) or source
        source = strip_trailing_slash(source)


    while destination == None or source == destination or not os.path.isdir(destination):
        print "Desintation folder does not exist!"
        new_dest = raw_input("Desitination folder(%s): " % (destination)) or destination
        new_dest = strip_trailing_slash(new_dest)

        if source == new_dest:
            print "Desintation folder must be different to Source folder!"
            print "Source: %s" % source
            continue

        destination = new_dest

    # resolve relative paths to absolute paths
    if not re.search('^/', source):
        source = os.path.realpath(source)

    if not re.search('^/', destination):
        destination = os.path.realpath(destination)


    cls(3)
    print "Source folder: %s" % config('src')
    print "Destination folder: %s" % config('dst')

    log_file_name = config('log_filename')
    config_path = "%s%s%s" % (destination, slash(), config_filename)
    config_exists = os.path.isfile(config_path)


    if delete_config_file:
        config_exists = False

    # generate web monitor assets
    # requires the destination path and .mkproxy folder
    if config_exists and create_web_assets:
        create_web_monitor(destination)
        halt()

    if config_exists:
        config_dct.update(json.loads(open(config_path, 'r').read()))

        # update local references
        config('src', source)
        config('dst', destination)
        config('worker', worker_id)
        config('worker_addr', worker_addr)

        print "Config exists. Participate as worker thread \"%s\" (%s)" % (config('worker'), config('worker_addr'))

        # confirm rel path to src and dst
        log_file_name = config('log_filename')

    cls(2)
    print "Collect FFMPEG prores settings:"
    config('prores_encoder', get_input('Which prores encoder', 'string', ['prores_ks', 'prores', 'prores_aw'], config_exists))
    config('prores_profile', get_input('Which prores profile -- 0:Proxy, 1:LT, 2:SQ and 3:HQ', 'string', ['0', '1', '2', '3'], config_exists))
    config('prores_quality', get_input('Quality -- 0:high to 32:low', 'number', [15, 0, 32], config_exists))
    config('transcode', get_input('Transcode -- \"all\", \"no\" OR list', 'array', ['all', 'none'], config_exists))
    config('dimensions', get_input('Resize -- \"no\" OR (WIDTH)x(HEIGHT)', 'dimension', ['1920x1080', '1280x720', '1920x1080', '2560x1440', '3840x2160', '7680x4320'], config_exists))
    config('gig_limit', get_input('Skip large files -- 0 = No Gig limit', 'number', [20, 0, 999], config_exists))
    config('byte_limit', int(float(config('gig_limit'))*gigabyte))



    if not config_exists:

        # create a config file for slave nodes
        cls(2)
        asset_folder = config_path.replace("config.json", '')
        print "Create NEW config file:\n", get_prefix(config_path)
        # create the asset folder
        if not os.path.isdir(asset_folder):
            print "Create folder:", asset_folder
            try:
                os.makedirs(asset_folder)
            except:
                msg = tsv("ERROR", "Can't asset folder", asset_folder)
                if not errors.count(msg):
                    errors.append(msg)
                    append_to_log(msg)
                halt()


        config_file = open(config_path, 'w')
        config_file.write(json.dumps(config_dct, indent=4))
        config_file.close()

        create_ffmpeg_files = True

        # create the log file
        append_to_log(tsv("TYPE", "DESCRIPTION", "VALUE", "COMMENT"))
        append_to_log(tsv("INFO", "input", source))
        append_to_log(tsv("INFO", "output", destination))
        append_to_log(tsv("INFO", "encoder", config('prores_encoder')))
        append_to_log(tsv("INFO", "profile", config('prores_profile')))
        append_to_log(tsv("INFO", "quality", config('prores_quality')))
        append_to_log(tsv("INFO", "dimensions", config('dimensions')))
        append_to_log(tsv("INFO", "size limit", config('byte_limit'), sizeof_fmt(config('byte_limit'))))


    # load ignore directory list
    ignore_folders = get_ignored_folders()


    if create_ffmpeg_files:
        create_meta_data()
        present_warnings()
        if len(stack):
            cls(2)
            print "There are %d items ready to transcode." % (len(stack))
            if raw_input("Do you want to continue: (y/N) ") != 'y':
                halt()

    transcode_footage()
    summary_report()

