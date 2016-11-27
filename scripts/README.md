# transcode

- Recursively scan the SOURCE volume and mirror the file structure into the DESTINATION volume
- Create a "config.json" file for the worker nodes to reference. The config file stores:
    - FFMPEG options for transcoding the media.
    - relative path to the DESTINATION media file
    - last_modified timestamp (for clean-up)