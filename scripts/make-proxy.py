import os, sys, re, subprocess, time, datetime, json, argparse
from distutils.spawn import find_executable
from string import Template


def cls(n=None):
    # os specific "clear"
    # or line feeds
    method = 'cls' if os.name == 'nt' else 'clear'
    if n == None or n < 1:
        os.system(method)
        return
    print "\n"*n

def slash():
    delim = "\\" if os.name == 'nt' else "/"
    return delim

def folder_fix(path, char=None):
    if char == None: char = slash()
    if char == '\\': char += char #regex escape "\"
    fix_path = re.sub('[\\\/]', char, path)
    # print "FOLDER-FIX", char, path, fix_path
    return fix_path

def tsv(type='NONE', desc="No description", value='', extra=''):
    return "%s\t%s\t%s\t%s" % (type.ljust(8), desc, value, extra)

def sizeof_fmt(num, suffix='B'):
    for unit in ['','K','M','G','T','P','E','Z']:
        if abs(num) < 1024.0:
            return "%3.2f %s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)

def now(style='%Y/%m/%d %H:%M:%S'):
    if style == 'time': style = '%H:%M:%S'
    if style == 'filename': style = '%Y%m%d_%H%M%S'
    return str(datetime.datetime.now().strftime(style))



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

    command += ['-s', config('dimentions')]
    command += ['-threads', '0', '-hide_banner', '-y']

    command += ['-metadata comment="ORIGINAL: %s"' % (input_filename)]
    command += ['"%s.part.mov"' % output_filename]
    return ' '.join(command)

def get_bash_script(input_relative, output_relative):

    bash_string = [
        input_relative,
        output_relative
    ]

    return '\n'.join(bash_string)


def ignore_folder(path):
    global ignore_folders

    path = pipe_path(path)
    path = re.sub('^\|+|\|+$', '', path.strip())
    paths = path.split('|')
    cat = '|'
    match = False
    for folder in paths:
        cat += folder + '|'
        if match == False and ignore_folders.has_key(cat):
            print "MATCHED INGORE: %s" % (cat)
            match = True

    return match

def create_output_assets():

    global file_count
    global total_bytes
    global ignore_folders

    source = str(config('src'))
    destination = str(config('dst'))

    print "ignore_folders", ignore_folders

    for root, subdirs, files in os.walk(source):
        for file in files:

            # skip dot files (eg ._myVideoFile.MOV)
            if re.compile("^\.").match(file):
                continue


            input_filename = "%s/%s" % (root, file)
            input_extension = re.search('([a-z0-9]+)$', input_filename, re.IGNORECASE).group(0)
            input_file_size = os.path.getsize(input_filename)

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

            # skip ignored folders
            if (ignore_folder(base_folder)):
                msg = tsv("IGNORE", "Ignore base folder", base_folder)
                if not errors.count(msg):
                    errors.append(msg)
                    append_to_log(msg)
                continue

            # skip non-video media
            if not is_video.match(file):
                continue

            # skip large files
            byte_limit = config('byte_limit')
            if (byte_limit > 0) and (input_file_size > byte_limit):
                errors.append(tsv("WARN", "Size limit exceeded", base, sizeof_fmt(input_file_size)))
                append_to_log(tsv("WARN", "Size limit exceeded", base, sizeof_fmt(input_file_size)))
                continue

            # skip existing transcoded files
            if skip_existing_files and os.path.isfile(output_filename):
                errors.append(tsv("SKIP", "Output media exists", output_filename))
                append_to_log(tsv("SKIP", "Output media exists", output_filename))
                continue

            # is this a transcode (ie input does not match output)
            if input_extension.lower() != output_extension.lower():
                errors.append(tsv("TRANS", "Transcode media", input_filename , "%s to %s" % (input_extension,output_extension)))
                append_to_log(tsv("TRANS", "Transcode media", input_filename , "%s to %s" % (input_extension,output_extension)))

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
                try:
                    bash_file = open("%s.ffmpeg" % (output_filename), 'w')
                    bash_string = get_bash_script(input_rel, output_rel)
                    bash_file.write(bash_string)
                    bash_file.close()
                    file_count += 1
                    total_bytes += input_file_size
                    new_row = [bash_string, input_filename, output_filename]
                    print "ADDED", input_filename, len(stack)
                    stack.append(new_row)
                    append_to_log(tsv("ADDED", "Added media file", input_filename))
                except:
                    # errors.append("Can't create file (%s.ffmpeg)" % (output_filename))
                    errors.append(tsv("ERROR", "Can't create command file", "%s.ffmpeg" % (output_filename)))
                    append_to_log(tsv("ERROR", "Can't create command file", "%s.ffmpeg" % (output_filename)))

    append_to_log(tsv("INFO", "File count", file_count))
    append_to_log(tsv("INFO", "Total bytes", sizeof_fmt(total_bytes)))

    return

def append_to_log(text, filename=None):
    global log_file_name
    destination = config('dst')
    filename = filename or log_file_name
    log_file = open("%s/%s" % (destination, filename), 'ab+')
    log_file.write('\n'+text)
    print "LOG:", text
    log_file.close()

def present_warnings():
    if len(errors):
        print "-------------------------------------------"
        print " WARNINGS that occured while preparing"
        print "-------------------------------------------"
        print "\n - " + ('\n - '.join(errors))
    return

def get_next_task():
    # returns a FFMPEG command file
    destination = str(config('dst'))
    work = []

    for root, subdirs, files in os.walk(destination):
        for file in files:
            filename = "%s%s%s" % (root, slash(), file)
            if re.search('ffmpeg$', file):
                print "work file found: ", file, re.search('ffmpeg$', file)
                work.append(filename)
                append_to_log(tsv('WORK', "work file found: ", file))
                break
        if len(work): break

    if len(work):
        return work[0]

    return None

def create_proxy_footage():
    global which_ffmpeg

    src = config('src')
    dst =  config('dst')
    task_filename = get_next_task()

    append_to_log(tsv('WORKER', 'Worker joined ... ', config('worker'), now()))
    while task_filename:

        base_filename = re.sub('.ffmpeg$', '', task_filename)
        base_filename = re.sub(dst, '', base_filename)
        print "BASE filename:", base_filename
        src_filename = src + base_filename
        dst_filename = dst + base_filename
        print "doing this ....", task_filename, src_filename, dst_filename
        os.rename(task_filename, task_filename+'.locked')
        work_time = now('time')
        work_worker = config('worker')
        append_to_log(tsv('WORK', 'Start transcoding', task_filename, "%s %s" % (work_worker, work_time)))

        # open the task file and extract src, dest and
        # add create the relative paths for the batch command
        task_file = open(task_filename+'.locked', 'r').read()
        task_file = task_file.split('\n')

        abs_input = src + task_file[0]
        abs_output = dst + task_file[1]
        task_cmd =  get_ffmpeg_command(abs_input, abs_output)


        # print "Executing %d of %d (%d%%)\n\n" % (i, n, int((float(i-1)/float(n)) * 100))
        subprocess.call(task_cmd, shell=True)
        print "\n"*5
        print "transcoding done"
        print "doing this ....", task_filename, abs_input, abs_output
        work_time = now('time')

        # clean-up: rename temp file
        if os.path.isfile(abs_output + '.part.mov'):
            print "Rename partial file", dst, abs_output
            os.rename(abs_output + '.part.mov', abs_output)
            input_size = os.path.getsize(abs_input)
            output_size = os.path.getsize(abs_output)
            ratio = float(output_size)/float(input_size)
            append_to_log(tsv('WORK', 'Finished transcoding', task_filename, "%s %s %2.2f" % (work_worker, work_time, ratio)))

            # delete ffmpeg command file IF transcode was successful
            if os.path.isfile(abs_output +'.ffmpeg.locked'):
                print "Delete FFMPEG bash script"
                os.remove(abs_output + '.ffmpeg.locked')
                cls()
        else:
            msg = tsv("FAIL", "Failed to create output media", abs_output)
            append_to_log(msg)
            print msg
            time.sleep(5)
            cls(5)

        # loop to next file ... or exit
        # print "finished .. zzzzzzz"
        # time.sleep(20)
        task_filename = get_next_task()

    append_to_log(tsv('WORKER', 'Worker left ... all done', config('worker'), now()))


def pipe_path(path):
    path = path.strip()
    return re.sub('[\\\/]', '|', path)

def get_ignored_folders():
    folder = str(config('dst'))
    file_name = "%s%s.ignore" % (folder, slash())
    lines = {}
    try:
        file = open(file_name, 'r')
        append_to_log(tsv("INFO", "Ignore file found"))
        for line in file:
            clean_path = pipe_path(line)
            lines[clean_path] = True
    except:
        append_to_log(tsv("INFO", "Nothing to ignore"))

    return lines

def config(key, value=None):
    global config_dct
    # returns config value
    if value != None:
        config_dct[key] = value

    value = config_dct[key]
    if type(value) is unicode:
        value = value.encode('ascii')

    return value

if __name__ == "__main__":


    parser = argparse.ArgumentParser()
    parser.add_argument("-i", type=str, help="(String) Source folder to scan for video assets")
    parser.add_argument("-o", type=str, help="(String) Destination folder for the transcoded media")
    parser.add_argument("-d", action="store_true", help="Delete and re-create the config file.")
    parser.add_argument("-n", type=str, help="Name the worker, used in the event log")


    args = parser.parse_args()

    cwd = os.getcwd()
    source = args.i or "../sample/src"
    destination = args.o or "../sample/dst"
    worker_id = args.n or str("worker_" + now('filename'))
    delete_config_file = args.d

    # resolve relative paths to absolute paths
    if not re.search('^/', source):
        source = os.path.realpath(source)

    if not re.search('^/', destination):
        destination = os.path.realpath(destination)


    # sys.exit(0)

    # global variables
    config_filename = "config.json"
    config_dct = {
        "src": source,
        "dst": destination,
        "prores_encoder": 'prores_ks',  # 'prores' 'prores_ks' (supports 4444) 'prores_aw'
        "prores_profile": "0", # 0:Proxy, 1:LT, 2:SQ and 3:HQ
        "prores_quality": "15", # huge file: [0 |||||| 9-13 |||||||| 32] terrible quality
        "dimentions": '1920x1080',
        "gig_limit": 20,
        "byte_limit": None,
        "total_files": 0,
        "total_bytes": 0.0,
        "total_progress": 0,
        "worker": worker_id,
        "date_created": str(datetime.datetime.now().strftime('%Y/%m/%d %H%M%S'))
    }
    # the most common video extensions to match and convert
    is_video = re.compile('.*(mp4|mov|qt|avi|wmv|m4v|mpeg|3gp|mxf|mkv)$', re.IGNORECASE)
    log_file_name = "event_log_%s.csv" % (now('%Y%m%d_%H%M'))
    which_ffmpeg = find_executable("ffmpeg")
    gigabyte = 1024**3
    stack = [] # the FFMPEG execution stack
    errors = [] # the collated runtime errors
    info = [] # the information feedback log file
    file_count = 0
    total_bytes = 0
    skip_existing_files = True
    create_ffmpeg_files = False


    config_path = "%s%s%s" % (destination, slash(), config_filename)
    config_exists = os.path.isfile(config_path)

    if delete_config_file:
        config_exists = False

    if config_exists:
        config_dct.update(json.loads(open(config_path, 'r').read()))

        cls()
        config('worker', worker_id)
        print "Config exists"
        print "Participate as worker thread \"%s\"" % config('worker')

        # confirm rel path to src and dst
        if config('src') != source:
            config_dct['src'] = raw_input("Source folder(%s): " % (source)) or source
        if config('dst') != destination:
            config_dct['dst'] = raw_input("Desitination folder(%s): " % (destination)) or destination

        config_dct['src'] = re.sub('[\\\/]+$', '', config('src'))
        config_dct['dst'] = re.sub('[\\\/]+$', '', config('dst'))


    else:

        # config_dct['None'] = 'None'
        config_dct['src'] = raw_input("Source folder(%s): " % (source)) or source
        config_dct['dst'] = raw_input("Desitination folder(%s): " % (destination)) or destination

        config_dct['prores_encoder'] = raw_input("Which prores encoder (%s) 'prores', 'prores_ks', 'prores_aw': " % (config('prores_encoder')) ) or config('prores_encoder')
        config_dct['prores_profile'] = raw_input("Which prores profile (%s) 0:Proxy, 1:LT, 2:SQ and 3:HQ: " % (config('prores_profile')) ) or config('prores_profile')
        config_dct['prores_quality'] = raw_input("Quality (%s) 0:high to 32:low: " % (config('prores_quality')) ) or config('prores_quality')
        config_dct['dimentions'] = raw_input("Output dimenstions (%s): " % (config('dimentions')) ) or config('dimentions')

        new_gig_limit = raw_input("Skip large files (%s GB): " % (config('gig_limit')) )
        gig_limit = float(new_gig_limit or config('gig_limit'))
        config_dct['gig_limit'] = int(gig_limit)
        config_dct['byte_limit'] = gig_limit*gigabyte

        # strip trailing "/"
        config_dct['src'] = re.sub('[\\\/]+$', '', config('src'))
        config_dct['dst'] = re.sub('[\\\/]+$', '', config('dst'))

        # create a config file for slave nodes
        cls()
        print "creating new config file", config_path
        config_path = "%s%s%s" % (destination, slash(), config_filename)
        config_file = open(config_path, 'w')

        config_file.write(json.dumps(config_dct, indent=4))
        config_file.close()

        create_ffmpeg_files = True

        append_to_log(tsv("TYPE", "DESCRIPTION", "VALUE", "COMMENT"))
        append_to_log(tsv("INFO", "input", source))
        append_to_log(tsv("INFO", "output", destination))
        append_to_log(tsv("INFO", "encoder", config('prores_encoder')))
        append_to_log(tsv("INFO", "profile", config('prores_profile')))
        append_to_log(tsv("INFO", "quality", config('prores_quality')))
        append_to_log(tsv("INFO", "dimensions", config('dimentions')))
        append_to_log(tsv("INFO", "size limit", config('byte_limit'), sizeof_fmt(config('byte_limit'))))


    ignore_folders = get_ignored_folders()

    if create_ffmpeg_files:
        create_output_assets()
        present_warnings()
        if len(stack):
            print "\n\n\nThere are %d items ready to transcode." % (len(stack))
            if raw_input("Do you want to continue: (y/N) ") != 'y':
                sys.exit(0)

    create_proxy_footage()

