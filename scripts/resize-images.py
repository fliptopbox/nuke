import os, sys, re, PIL
from PIL import Image


input_root = "/media/bruce/mega/solo-on-moto/media/images"
output_root = "/home/bruce/Desktop/stills"


is_image = re.compile('.*(jpg|jpeg|gif|png|tif)$', re.IGNORECASE)
abs_max_px = 4096 # absolute max height or width
errors = []

def tsv(type='NONE', desc="No description", value='', extra=''):
    return "%s\t%s\t%s\t%s" % (type.ljust(8), desc, value, extra)

for root, subdirs, files in os.walk(input_root):
    for file in files:

        input_filename = "%s/%s" % (root, file)
        base =  input_filename.replace(input_root, "")
        output_folder = ("%s%s" % (output_root, base)).replace(file, '')
        output_filename = output_folder + file

        # skip dot files (eg ._myVideoFile.MOV)
        if re.compile("^\.").match(file):
            print "skip dot file", file
            continue

        # only process still images
        if not is_image.match(file):
            print "not an image:", file
            continue

        # skip existing media
        if os.path.isfile(output_filename):
            print "skip existing media", file
            continue

        # process image object
        img = Image.open(input_filename)
        img_max_px = max(img.size[0], img.size[1])
        img_width = float(img.size[0])
        img_height = float(img.size[1])

        os.system('clear')
        print "\n\n"
        print "Output:", output_filename


        # create proxy output folder(s)
        if not os.path.isdir(output_folder):
            # print "Create folder:", output_folder
            try:
                os.makedirs(output_folder)
            except:
                msg = tsv("ERROR", "Can't create folder", output_folder)
                if not errors.count(msg):
                    errors.append(msg)
                continue

        if img_max_px > abs_max_px:
            resize_by = float(abs_max_px) / float(img_max_px)
            img_new_width = int(img_width * resize_by)
            img_new_height = int(img_height * resize_by)

            print "Reduce by: %s" % (resize_by)
            # print "Width - from:%f to:%f" % (img_width, img_new_width)
            # print "Height - from:%f to:%f" % (img_height, img_new_height)
            print "New dimensions: %dx%d" % (img_new_width, img_new_height)
            img.resize((img_new_width, img_new_height), PIL.Image.ANTIALIAS)

        img.save(output_filename)