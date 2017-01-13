

## dynamic transcoding

An option or flag that will instruct FFMPEG sub-process to change it parameters relative to the incoming codec. So that highly compressed media, like MP4s are not re-coded with bitrates that are beyond the source data bounds. It seems silly to encode a low res format with a high res codec.

## optimise network activity

At the moment the source media is on the host, and the partial file is constructedon the local /tmp/, this to improve network traffic. However it might be more efficiant to transfer the original media file to the local worker, then do the work, then copy the output media back to the remote host. Essentially to keep the network traffic to a minimum, this seems to deteriorate the entire transcoding network.

## global instructions

It would be great to have the ability to instuct all participants to halt transcoding, when they have finished their current task.

## limiting work load per node

Some machines on the network have lower capacity to do work. Perhaps it is a low spec machine, to it has network bandwidth restrictions, or perhaps a combination of both. It would be great if the network recorded each workers frames-per-second average, and for slower workers, adjusted the media relatively. So slow machines get smaller files.

## set-up/tear-down housekeeping

I have noticed that interupted scripts leave media in the /tmp/ folder. Media can be huge, and so as part of the initilization routine, temp assets should be flushed as a precaution.

