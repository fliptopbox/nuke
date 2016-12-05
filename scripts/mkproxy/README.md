# make proxy

A python script to transcode footage from a source folder into a destination folder, using FFMPEG to generate **Apple ProRes Proxy** files.

On first run, the script will gather the FFMPEG settings, and save them to a config file, then it creates *work* files, on the destination volume, so that additional workers can be employed to help with the transcoding workload, and finally, it creates an event log.

The log file contains the global transcode settings, the work files, errors and warnings regarding the work files, and a running commentary from worker threads, as the do their work.

The script also allows you to define an *ignore* file, to bypass unwanted folders.


### Usage example

**single worker**

	python make-proxy.py -i "/abs/path/to/source/" -o "/abs/path/to/destination/"

**multiple workers**

Intitalise work load, and name the priniciple worker "maya"

	python make-proxy.py -i "/local/source/" -o "/local/destination/" -n MAYA

... on the helper machines, named "willy" and "wally", mount the respective **source** and **desitination** folders for each worker, and run:

	python make-proxy.py -i "/mounted/source/" -o "/mounted/destination/ -n WILLY"
	python make-proxy.py -i "/volume/source/" -o "/volume/destination/ -n WALLY"

**Please note:**

* If your folder names contains spaces, please quote the path.
* The source folder MUST be different to the destination folder
* The folder structure, of the source, will be mirrored on the destination volume
* Existing media, in the output folder, will be preserved.

### Switches

The script has the following arguments

| Switch | Type  | Description                      | Notes
|------|---------|----------------------------------|------------------|
| -i   | Path   | Absolute path to input folder                        | Required
| -o   | Path   | Absolute path to output folder                       | Required
| -n   | String | Name of the worker                                   | Optional
| -d   | Switch | Delete existing config                               | Optional
| -w   | Switch | Start a web server monitor (on port 8000)            | Optional

### Config settings

| Setting   | Description                           | Default    |
|-----------|---------------------------------------|------------|
| encoder   | prores, prores_ks, prores_aw          | prores_ks
| profile   | 0: Proxy, 1: LT, 2: SQ and 3: HQ      | 0
| quality   | Number from 0 (high) to 32 (low)      | 20
| transcode | Transcode non-MOV media (all, no)     | all
| resize    | Force resize (no, WIDTHxHEIGHT)       | 1920x1080
| skip      | Bypass large files (in Gigs)          | 20

### Ignore folder list

Create "ignore.txt" file in the destination root folder, add one folder per line. Please ensure the path begins and ends with a "/". These are relative paths.

	/path/to/exclude/ # only media and subfolders in the "exclude" folder will be skipped
	/render/ # all contained media and subfolders will be skipped

The ignore.txt file should be created BEFORE the initial run. However all workers will try to load the ignore file when that start work.

### SimpleHTTP web monitor

If you have multiple workers on your network you might want to run the web monitor, to watch the activity. To do this run the following command on a machine connectted to the same network.

	python make-proxy.py -i /Volume/source -o /Volume/destination -w

A python simplified webserver will start-up and present you with an overview of the nodes, and easy access to the consolidated log file, so that you can check for errors and failures.

### System Requirements

- [Python version 2.7+](https://www.python.org/)
- [FFMPEG version 3.2](https://www.ffmpeg.org/)

