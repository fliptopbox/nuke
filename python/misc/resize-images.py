import os, sys, re, PIL
from PIL import Image


input_root = "/Volumes/titanium/som-original-images"
output_root = "/Volumes/silver/solo-on-moto/images/resize"


is_image = re.compile('.*(jpg|jpeg|gif|png|tif)$', re.IGNORECASE)
abs_max_px = 1920 # absolute max height or width
errors = []
images = []

def tsv(type='NONE', desc="No description", value='', extra=''):
    return "%s\t%s\t%s\t%s" % (type.ljust(8), desc, value, extra)

def resize(input_filename, output_filename):
    # process image object
    img = Image.open(input_filename)
    img_max_px = max(img.size[0], img.size[1])
    img_width = float(img.size[0])
    img_height = float(img.size[1])


    print "\nOutput:", output_filename


    if img_max_px > abs_max_px:
        resize_by = float(abs_max_px) / float(img_max_px)
        img_new_width = int(img_width * resize_by)
        img_new_height = int(img_height * resize_by)

        print "Reduce: %3.2f%% (max:%s) to: %s x %s" % (resize_by*100, abs_max_px, img_new_width, img_new_height)
        img.resize((img_new_width, img_new_height), PIL.Image.ANTIALIAS)

    img.save(output_filename)

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

        # create proxy output folder(s)
        if not os.path.isdir(output_folder):
            print "Create folder:", output_folder
            try:
                os.makedirs(output_folder)
            except:
                msg = tsv("ERROR", "Can't create folder", output_folder)
                print msg
                continue

        # and image in/out to work stack
        images.append([input_filename, output_filename])

# iterate over stack
total_work = len(images)

while len(images):
    image_in, image_out = images.pop(0)
    resize(image_in, image_out)
    os.system('clear')
    p = 100.0 - float(len(images))/float(total_work) * 100
    print "%s of %s (%2.1f%%)\n%s" % (total_work - len(images), total_work, p, ('|'*int(p)).ljust(100, ':'))

