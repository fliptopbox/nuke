## Bash scripts

### Installing ImageMagick with openExr support

For mac user on "El Capitan", you will need to ensure you have the most up-to-date version of Xcode (v7.2.1) and home-brew (v0.9.5) installed and working before you continue.

	# install openEXR
	brew install openexr

	# install imagemagic (with EXR support)
	brew install imagemagick --with-openexr

	# check "openexr" is configured
	convert -list configure | grep DELEGATES

### Batch convert EXR

Loop through a directory of .exr files, and convert them to .jpg, and delete the massive original so that you can keep disk space low.

	#!/bin/bash/

	for ME in *.exr;
	do
      	# the "&&" stops the delete if errors occur
		convert $ME ${ME%.exr}.jpg && rm $ME && echo "$ME complete"
	done
	
	
### Text file as bash array

Open a text file, and use the contents as an array to rename files so that they correspond to the list in the text file.

	for LINE in $(< ordered_list.txt)
	do
		(bash commands);
	done;


### Convert Sony-F55 XAVC footage into ProRes HQ 422 MOV clips

Run this bash script in the source folder, where you have collected all the MXF files. Change the output folder to taste.
This loop will iterate over all the MXFs and convert them to MOVs, please note that the 1st and 2nd audio channels will be swapped in the output clip.

Kudos goes out to Wayne Poll who solved the audio problem and is the source of this solution.

https://ffmpeg.org/pipermail/ffmpeg-user/2013-June/015751.html


	#!/bin/bash/

	for ME in *.MXF;
	do
	        ffmpeg -i $ME -map 0 -map -0:9:0 -c copy -c:v prores -profile:v 3 /media/bruce/helium/media/sony-f55/${ME%.MXF}.mov
	done;

### Convert a still JPG to MOV seuence
Requires FFMPEG and SED (for regex in bash)

Usage:
Create a bach script (jpg_to_mov.sh) in the folder that contains the JPG assets. Run the script with 'sh jpg_to_mov.sh'

The script will create two folders, 'jpg' and 'mov', ffmpeg will create the MOV in the 'mov' folder for each asset, and on completion the JPG will be moved to the 'jpg' folder.

When the script is finished, it will delete itself from the root folder.

	#!/bin/bash/

    # create folders
    mkdir "mov"
    mkdir "jpg"

    FPS=24
    DURATION=4
    QUAL=15

    # loop over all jpeg images
    for ME in *.JPG *.jpg *.jpeg;
    do
        # create output filename
        OUTPUT=$(sed 's/JPG/mov/g; s/jpg/mov/g; s/jpeg/mov/g' <<< $ME);

        # generate the MOV
        clear
    	echo "\n\n\nConverting: $ME to $OUTPUT\n\n"
    	ffmpeg -hide_banner -framerate $FPS -loop 1 -i "$ME" -vf "scale=1920:-1,crop=1920:1080"  -c:v prores_ks -profile:v 1 -qscale $QUAL -t $DURATION -pix_fmt yuv422p10le "mov/$OUTPUT"

        # move original image into JPG folder
        mv "$ME" "jpg/$ME"

    done;

    # clean-up
    rm 'jpg_to_mov.sh'