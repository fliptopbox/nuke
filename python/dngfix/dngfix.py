'''
    D N G F I X
    This is a utility script to generate dropped frames in DNG sequences.
    The script runs recursively on a directory and it's sub-directories,
    and creates dropped frames by duplicating the last available DNG.

    Usage:
    python dngfix.sh -i "footage/BMCC/"
'''
import os, sys, re, shutil, argparse

def version ():
    major = 0
    minor = 1
    build = 19
    ver = [str(major), str(minor), str(build)]
    return '.'.join(ver)

def cls(n=None):
    # os specific "clear"
    # or line feeds
    method = 'cls' if os.name == 'nt' else 'clear'
    if n == None or n < 1:
        os.system(method)
        banner()
        return
    print "\n"*n

def banner():
    print "\nD N G F I X (version:%s)\n\n" % version()

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

def create_dropped_frames(folder_root, max_frame, frame_digits, frame_dictionary):
    x = i = last_frame = 0
    missing_files = []
    folder_path = folder_root.split('/')
    file_base = folder_path[-1]

    for i in range(0, max_frame):
        if not i in frame_dictionary:

            src = folder_fix(folder_root, "%s_%s.dng" % (file_base, str(last_frame).rjust(frame_digits, '0')))
            dst = folder_fix(folder_root, "%s_%s.dng" % (file_base, str(i).rjust(frame_digits, '0')))

            print "Frame: %s derived from  '%s'" % (str(i).rjust(frame_digits, '0'), src)
            # print "src", src, "dst", dst

            shutil.copyfile(src, dst)
            missing_files.append(i)
            x += 1
            continue

        last_frame = i

    # print "Created frames:\n", missing_files
    print "DONE\n\n"


if __name__ == "__main__":

    cls()
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", type=str, help="(String) Source folder to scan for video assets")

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

    # derive the base file name, based on folder name
    # i = x = 0
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
            print "Detected dropped frames in \"%s\"" % (root)
            print "Sequence has %s frames of an expected %s. (dropped %s frames)" % (len(frame_dictionary), max_frame + 1, has_missing_frames)

            frame_digits = len(max_string)
            create_dropped_frames(root, max_frame, frame_digits, frame_dictionary)
            print "\n\n"

    print "\n\nFinished."
