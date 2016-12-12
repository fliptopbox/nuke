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

