# D N G F I X

This is a utility script, writen in Python 2.7 to fix broken DNG sequences caused by dropped frames.

The script runs recursively, on a directory and it's sub-directories, and finds sequences with dropped frames. The script fixes the gaps in the frame range, by duplicating existing DNG images until the sequence is restored.

A summary log file is created in each repaired folder, which lists missing assets and the file(s) used to derive the respective replacements.

Created by [fliptopbox](https://github.com/fliptopbox/)

## Requirements

- Python 2.7

## Usage

1. Download the file called "dngfix.py", when it is done, copy it to your footage folder.
2. Open a terminal in the same folder, and run the script by typing: python dngfix.py

There are two ways to execute the script, you can specify an input folder, or run it from the current directory

### Specify the input folder (local or network)
To specify a folder, use the -i switch like this .... oh and please do yourself a massive favour and quote the directroy path, because some OSes do not like spaces in files names, and that will cause great sadness. Stay happy, quote the path.

    python dngfix.py -i "footage/BMCC/"

### Run on local folder
OR you can run it from the current working direcorty (CWD) like this ...

    python dngfix.py

### Dry run (do not generate files)
If you do not want to generate missing files, you can dry-run with the "n" switch. This will generate the respective log file, without generating the missing files.

    python dngfix.py -n


### An example output

This was run in a folder with 3 DNG sequences (ie 3 sub-folders). One: has 5 arbitarty single dropped frames, the seconds: has 5 consequtive missing frames and the last: has nothing wrong with it.

    D N G F I X (version:0.1.19)


    Detected dropped frames in "dng/ftbx_1_2017-04-06_1414_C0001"
    Sequence has 285 frames of an expected 290. (dropped 5 frames)
    Frame: 000004 derived from  'dng/ftbx_1_2017-04-06_1414_C0001/ftbx_1_2017-04-06_1414_C0001_000003.dng'
    Frame: 000018 derived from  'dng/ftbx_1_2017-04-06_1414_C0001/ftbx_1_2017-04-06_1414_C0001_000017.dng'
    Frame: 000022 derived from  'dng/ftbx_1_2017-04-06_1414_C0001/ftbx_1_2017-04-06_1414_C0001_000021.dng'
    Frame: 000031 derived from  'dng/ftbx_1_2017-04-06_1414_C0001/ftbx_1_2017-04-06_1414_C0001_000030.dng'
    Frame: 000048 derived from  'dng/ftbx_1_2017-04-06_1414_C0001/ftbx_1_2017-04-06_1414_C0001_000047.dng'
    DONE


    Detected dropped frames in "dng/ftbx_1_2017-04-06_1734_C0006"
    Sequence has 320 frames of an expected 325. (dropped 5 frames)
    Frame: 000011 derived from  'dng/ftbx_1_2017-04-06_1734_C0006/ftbx_1_2017-04-06_1734_C0006_000010.dng'
    Frame: 000012 derived from  'dng/ftbx_1_2017-04-06_1734_C0006/ftbx_1_2017-04-06_1734_C0006_000010.dng'
    Frame: 000013 derived from  'dng/ftbx_1_2017-04-06_1734_C0006/ftbx_1_2017-04-06_1734_C0006_000010.dng'
    Frame: 000014 derived from  'dng/ftbx_1_2017-04-06_1734_C0006/ftbx_1_2017-04-06_1734_C0006_000010.dng'
    Frame: 000015 derived from  'dng/ftbx_1_2017-04-06_1734_C0006/ftbx_1_2017-04-06_1734_C0006_000010.dng'
    DONE



    Finished.