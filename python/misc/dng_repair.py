import os, sys, re, shutil, argparse




parser = argparse.ArgumentParser()
parser.add_argument("-i", type=str, help="(String) Source folder to scan for video assets")

args = parser.parse_args()


# folder_root = "/home/bruce/Desktop/BMPCC/ftbx_1_2017-04-06_1719_C0000"
folder_root = args.i or None

if not folder_root:
	print "require source folder"
	sys.exit(0)


if not os.path.isdir(folder_root):
	print "Source folder does not exist"
	sys.exit(0)


folder_path = folder_root.split('/')
file_base = folder_path[-1]

print "\n\nBase File Name:\n", file_base, "\n"


i = x = 0

max_frame = 0
max_string = ''


frame_number = re.compile('(.*)_([^\.]+)(\.dng)')
frame_dictionary = {}

for root, subdirs, files in os.walk(folder_root):
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

print "Summary of missing files:"
print "Total files:", len(frame_dictionary)
print "Max frame number:", max_frame
print "Missing frames:", max_frame - len(frame_dictionary)

missing_files = []

for i in range(0,max_frame):
	if not i in frame_dictionary:
		# print x+1, 'missing', i, last_frame, "%s_%s.dng" % (file_base, str(i).rjust(6, '0'))
		
		src = "%s/%s_%s.dng" % (folder_root, file_base, str(last_frame).rjust(6, '0'))
		dst = "%s/%s_%s.dng" % (folder_root, file_base, str(i).rjust(6, '0'))

		shutil.copyfile(src, dst)
		missing_files.append(i)
		# print src, dst
		x += 1
		continue

	last_frame = i

print "\n\nCreated DNG frames for ..."
print missing_files