# D N G F I X

This is a utility script to generate dropped frames in DNG sequences.

The script runs recursively on a directory and it's sub-directories, and fixes broken sequences dropped frames by duplicating the last available DNG, until the gap is closed

### Usage:

You can specify the input folder like this ....

    python dngfix.py -i "footage/BMCC/"

OR run it from the current working direcorty

    python dngfix.py

