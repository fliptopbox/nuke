# NukeX

Here are some things I have started to collect that replace to Nuke, and linux. Things that I fin myself forgetting, and looking up on google over and over.

## Nuke snippets

**[ColorEdge](ColorEdge.txt)** is a node group that is fantastic tool for marker removal.


## Bash scripts

Loop through a directory of .exr files, and convert them to .jpg, and delete the massive original so that you can keep disk space low.

	for ME in *.exr;
	do
		convert $ME ${ME%.exr}.jpg;
		rm $ME;
	done;

Open a text file, and use the contents as an array to rename files so that they correspond to the list in the text file.

	for LINE in $(< ordered_list.txt)
	do
		(bash commands);
	done;