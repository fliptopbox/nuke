'''
    D N G F I X

    by fliptopbox 
    https://github.com/fliptopbox/

    This is a utility script, writen in Python 2.7 to 
    fix broken DNG sequences caused by dropped frames.
    The script runs recursively, on a directory and it's 
    sub-directories, and finds sequences with dropped 
    frames. The script fixes the gaps in the frame 
    range, and generates a summary log file.

    Usage:
    python dngfix.sh -i "footage/BMCC/"
    python dngfix.sh -n # (dry run) report missing files
'''
import os, sys, re, shutil, argparse

def version ():
    major = 0
    minor = 2
    build = 13
    ver = [str(major), str(minor), str(build)]
    return '.'.join(ver)

def cls(n=None):
    # os specific "clear"
    # or line feeds
    method = 'cls' if os.name == 'nt' else 'clear'
    if n == None or n < 1:
        os.system(method)
        print banner()
        return
    print "\n"*n

def banner():
    return "\nD N G F I X (version:%s)\n\n" % version()

def strip_trailing_slash(path=''):
    if not path: return ''
    return re.sub('[\\\/]+$', '', path)

def folder_fix(path, *args):
    # add a ' ' to catch *nix absolute root
    parts = ' ' + path + '/' + '/'.join(args)
    parts = re.split('[\\\/]+', parts)
    parts = '/'.join(parts)
    parts = os.path.normpath(parts)
    return parts.strip()

def create_dropped_frames(folder_root, max_frame, frame_digits, frame_dictionary, create_dng):
    x = i = last_frame = 0
    missing_files = []
    log_array = []
    log_text = ""
    folder_path = folder_root.split('/')
    file_base = folder_path[-1]
    has_missing_frames = (max_frame + 1) - len(frame_dictionary)

    # initialize folder log
    # log_array.append(banner())

    log_array.append("Detected dropped frames in \"%s\"" % (root))
    log_array.append("Sequence has %s frames of an expected %s. (dropped %s frames)" % (len(frame_dictionary), max_frame + 1, has_missing_frames))
    log_array.append("Create missing DNG assets: %s" % (create_dng))

    print '\n', '\n'.join(log_array), '\n'

    for i in range(0, max_frame):
        if not i in frame_dictionary:

            # print "src", src, "dst", dst
            src = folder_fix(folder_root, "%s_%s.dng" % (file_base, str(last_frame).rjust(frame_digits, '0')))
            dst = folder_fix(folder_root, "%s_%s.dng" % (file_base, str(i).rjust(frame_digits, '0')))

            log_text = "Frame: %s derived from  '%s'" % (str(i).rjust(frame_digits, '0'), src)
            log_array.append(log_text)
            print log_text

            if create_dng:
                shutil.copyfile(src, dst)

            missing_files.append(i)
            x += 1
            continue

        last_frame = i

    # write the log file
    log_array = [banner()] + log_array
    log_name = folder_fix(folder_root, "%s.txt" % (file_base))
    log_file = open(log_name, "w")
    log_file.write('\n'.join(log_array))
    log_file.close()

    # print "Created frames:\n", missing_files
    # print "DONE\n\n"
    # return missing_files


if __name__ == "__main__":

    cls()
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", type=str, help="(String) Source folder to scan for video assets")
    parser.add_argument("-n", action='store_false', help="(Switch) Do NOT create the DNG assets, this is a dry run")

    args = parser.parse_args()

    # check input arguments
    folder_root = args.i or os.getcwd()
    if not folder_root:
        print "Require source folder as -i argument"
        sys.exit(0)

    # check folder is valid
    folder_root = strip_trailing_slash(folder_root)
    if not os.path.isdir(folder_root):
        print "Source folder does not exist."
        sys.exit(0)


    # create_dng = False
    create_dng = args.n

    # derive the base file name, based on folder name
    folder_path = folder_root.split('/')
    file_base = folder_path[-1]
    frame_number = re.compile('(.*)_([^\.]+)(\.dng)')
    frame_digits = 6 # default "zero" padding ie. 000001

    for root, subdirs, files in os.walk(folder_root):
        # print "folder_root: %s %s" % (root, folder_root)

        max_frame = 0
        max_string = ''
        frame_dictionary = {}

        for file in files:

            # work on files in the frame sequence
            if frame_number.search(file):

                result = frame_number.search(file)
                current_string = result.group(2)
                current_frame = int(result.group(2))

                frame_dictionary[current_frame] = 1

                max_frame = max(current_frame, max_frame)
                if max_frame == current_frame:
                    max_string = current_string

        # NOTE: DNG sequences start on frame zero.
        has_missing_frames = (max_frame + 1) - len(frame_dictionary)
        if len(frame_dictionary) and  has_missing_frames > 0:

            frame_digits = len(max_string)
            create_dropped_frames(root, max_frame, frame_digits, frame_dictionary, create_dng)
            print "DONE.\n\n"

    print "\n\nFinished."
