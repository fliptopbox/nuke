# Dirty Alpha Workflow

So you get a bucket load of stills, from a client, and you have to pump out psuedo footage because Ken Burns is just not feeling the love. You are not alone. It is a thank less job, and after doing one properly I decided to make a hack. Here it is.

## A simple premise

To do the psudo track and zoom on a still image yon need two things.

- A background plate
- A whole load of alpha channels

And you are probably going to crack open Photoshop and do it all there, saving each cleaned up layer with a layer mask, which then gets aplied into an alpha channel. And if you need to make amends then you end up round tripping to Photoshop (or im my case GIMP)

As you accumulate layers the PSD swells up and that really annoys me. 

## Pixel math is your friend

What if you could achieve the same thing with just two layers in the PSD?
A single background plate, and a composite RGB that contained 4 alpha masks in one?

You can.

### Composite layers with background plate

This is the result you are after. The RED, GREEN and BLUE channels are added together over a BLACK background, to give you a RGB plate, which will be split into your FOREGROUND, MIDGROUND and BACKGROUND masks.

(screenshot - RGB plate)
(screenshot - original plate)

The result is saved as a layered file, ie. TIF, EXR or PSD and the first thing you do in Nuke is split the masks channel into seperate alpha channels which are applied to the original plate. So you should have a script that looks something like this.

(screenshot - NUKE script)

 