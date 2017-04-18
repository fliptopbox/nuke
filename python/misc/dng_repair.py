import os, sys, re, shutil, argparse

def strip_trailing_slash(path=''):
    if not path: return ''
    return re.sub('[\\\/]+$', '', path)

def create_dropped_frames(folder_root, max_frame, frame_digits, frame_dictionary):
	i = last_frame = 0
	missing_files = []
	file_base = folder_root[-1]
	print folder_root, max_frame, frame_digits, frame_dictionary
	for i in range(0,max_frame):
		if not i in frame_dictionary:
			
			src = "%s/%s_%s.dng" % (folder_root, file_base, str(last_frame).rjust(frame_digits, '0'))
			dst = "%s/%s_%s.dng" % (folder_root, file_base, str(i).rjust(frame_digits, '0'))

			shutil.copyfile(src, dst)
			missing_files.append(i)
			# print src, dst
			x += 1
			continue

		last_frame = i

	print "\n\nCreated DNG frames for ...\n", missing_files


parser = argparse.ArgumentParser()
parser.add_argument("-i", type=str, help="(String) Source folder to scan for video assets")

args = parser.parse_args()

# check input arguments
folder_root = args.i or None
if not folder_root:
	print "Require source folder as -i argument"
	sys.exit(0)

# check folder is valid
folder_root = strip_trailing_slash(folder_root)
if not os.path.isdir(folder_root):
	print "Source folder does not exist."
	sys.exit(0)

# derive the base file name, based on folder name
folder_path = folder_root.split('/')
file_base = folder_path[-1]


print "\n\nBase File Name:\n", file_base, "\n"


i = x = 0

max_frame = 0
max_string = ''


frame_number = re.compile('(.*)_([^\.]+)(\.dng)')
frame_dictionary = {}
frame_digits = 6 # default "zero" padding ie. 000001

for root, subdirs, files in os.walk(folder_root):
	print "folder_root: %s %s" % (root, folder_root)
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
			
			# print "%s -- (%s) %s -- %s (%s)" % (file, current_string, current_frame, max_frame, max_string)
	
	has_missing_frames = max_frame - (len(frame_dictionary)- 1)
	if len(frame_dictionary) and  has_missing_frames > 0:
		print "%s:" % (root)
		print "Summary of missing files:"
		print "Total number of files:", len(frame_dictionary)
		print "Maximum frame number:", max_frame
		print "Dropped frame count:", has_missing_frames

		frame_digits = len(max_string)
		create_dropped_frames(folder_root, max_frame, frame_digits, frame_dictionary)

