# NukeX

Here are some things I have started to collect that relate to Nuke, and linux. Things that I find myself forgetting, and looking up on google over and over.

## Nuke snippets

**[ColorEdge](ColorEdge.txt)** is a node group that is fantastic tool for marker removal.

**[Vkeyer](vkeyer.txt)** a very interesting way to de-spill using a second matte to inject overlapping values from the background plate. (kudos to victor perez)

**[IBK Stacked](IBKStackedV1.txt)** IBK color widgets stacked. My favorite keying technique, it manages to key really fine details. (kudos to tony lyons)

**[Dirty Alpha](dirtyAlphaWorkflowV1.md)** I use GIMP for matte painting stuff. Recently I decided to combine my mattes into a single additive layer, to keep the size of the PSD to an all time low. If you like pixel math and RGB channels then check this out. 

**[Paralaxative](paralaxativeV1.txt)** A base tempalte and alternative workflow for creating parax 3d environment, using concentic spheres instead of 2d cards. This workflow also demonstrates my dirty alpha workflow.

## Installing ImageMagick with openExr support

For mac user on "El Capitan", you will need to ensure you have the most up-to-date version of Xcode (v7.2.1) and home-brew (v0.9.5) installed and working before you continue.

	# install openEXR
	brew install openexr

	# install imagemagic (with EXR support)
	brew install imagemagick --with-openexr

	# check "openexr" is configured
	convert -list configure | grep DELEGATES

## Bash scripts

Loop through a directory of .exr files, and convert them to .jpg, and delete the massive original so that you can keep disk space low.

	#!/bin/bash/

	for ME in *.exr;
	do
      	# the "&&" stops the delete if errors occur
		convert $ME ${ME%.exr}.jpg && rm $ME && echo "$ME complete"
	done

Open a text file, and use the contents as an array to rename files so that they correspond to the list in the text file.

	for LINE in $(< ordered_list.txt)
	do
		(bash commands);
	done;

# Convert Sony-F55 XAVC footage into ProRes HQ 422 MOV clips

Run this bash script in the source folder, where you have collected all the MXF files. Change the output folder to taste.
This loop will iterate over all the MXFs and convert them to MOVs, please note that the 1st and 2nd audio channels will be swapped in the output clip.

Kudos goes out to Wayne Poll who solved the audio problem and is the source of this solution.

https://ffmpeg.org/pipermail/ffmpeg-user/2013-June/015751.html


	#!/bin/bash/

	for ME in *.MXF;
	do
	        ffmpeg -i $ME -map 0 -map -0:9:0 -c copy -c:v prores -profile:v 3 /media/bruce/helium/media/sony-f55/${ME%.MXF}.mov
	done;


	
# Sony RAW viewer

This workflow has been replaced by the FFMPEG script above. No more RAW viewer, no more Apple compressor.

Disable the input settings. Uncheck Input Settings, ASC-CDL and Viewer Settings. Then in the Export tab, set **Bake** to Input Setting Only

Open the EXR sequence in Nuke, and set the colorspace to **Rec709**
