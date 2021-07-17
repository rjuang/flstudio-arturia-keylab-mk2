# MIDI Script for Arturia Keylab 49/61/88 (Essential or mkII)

## Overview
The goal of this MIDI Script is to make Arturia Keylab (mkII or Essential) more friendlier to use with FL Studio. The script was recently ported to work with Essential keyboards (so it is safe to ignore the mkII naming).

## Really old demo (refer to the feature videos below for updated results)
[![](http://img.youtube.com/vi/Ts2SnW9r2fc/0.jpg)](http://www.youtube.com/watch?v=Ts2SnW9r2fc "Old Demo of Script")

Refer to this [playlist](https://youtube.com/playlist?list=PLet-RTUimaMTyzOR9OvTb7-DQWe5RmWY8) for the latest content covering different features of the midiscript functionality in shorter videos.


## Discussion Thread
There is a discussion thread you can provide feedback or ask questions at [here](https://forum.image-line.com/viewtopic.php?f=1994&t=243170)

## Discord Server
I can also be reached via [Discord](https://discord.gg/aqA8rnnTFp)


## Setting Up
Video link describing setup below:

### Windows Setup Video ###
[![](http://img.youtube.com/vi/KUNfQjWnZwc/0.jpg)](http://www.youtube.com/watch?v=KUNfQjWnZwc "Setup instructions for Windows users")

### Mac Setup Video ###
[![](http://img.youtube.com/vi/woxzfQc238s/0.jpg)](http://www.youtube.com/watch?v=woxzfQc238s "Setup instructions for Mac users")

You can simply clone this project into the folder:
``` 
Documents/Image-Line/FL Studio/Settings/Hardware/
```
Then in FL Studio, goto `Options->Midi Settings` and select your Arturia device (the DAW one) under
`Input` section.

IMPORTANT: Make sure the scripts are in a subfolder within the Hardware folder. Otherwise, FL Studio will ignore the
files.

### For Macs ###

Follow the tips and instructions [here](https://www.arturia.com/faq/keylabmkii/keylab-mkii-tips-tricks) for setting
up the ports correctly.  Scroll down to "FL Studio" section at the very bottom of the link.

In the instructions, instead of selecting "Mackie Control Universal" select my script
`Arturia Keylab mkII DAW (MIDIIN2/MIDIOUT2)` under the scripts column.

Note that there will be another script called `Arturia Keylab mkII (MIDI)`. This is an optional script for enabling
Analog Lab. You can set `Keylab mkII XX MIDI` to this script. 

## For Windows ##
Follow the tips and instructions [here](https://www.arturia.com/faq/keylabessential/keylab-essential-tips-tricks) for
setting up the ports correctly. These are instructions for Keylab essential but the setup is the same as Keylab mkII.
I reference this one because it has a screenshot from a Windows setup.

In the instructions, instead of selecting "Mackie Control Universal" select my script
`Arturia Keylab mkII DAW (MIDIIN2/MIDIOUT2)` under the scripts column.

Note that there will be another script called `Arturia Keylab mkII (MIDI)`. This is an optional script for enabling
Analog Lab. You can set `Arturia Keylab mkII` device to this script. 

## IMPORTANT ##
When using your keyboard, make sure that you set it to use the DAW mode (i.e., the DAW button is selected as opposed to
the User or Analog Lab buttons).

If you would like to use Analog Lab plugins and control it with the "Analog Lab" mode button, you can use the optional
script provided here. FL Studio 20.8 also provides a native script to do this, but it has a known issue where by 
sustain pedal notes will be suppressed. Using either script, you'll still need to configure Analog Lab plugin's MIDI In
port to 10. This needs to be done for each plugin that is to be controlled with Analog Lab mode.
TODO: Add video explaining this. Refer to this [link](https://forum.image-line.com/viewtopic.php?f=100&t=245527&p=1569738#p1566027)

## Features

### Navigation Panel and Controls ###

[![](http://img.youtube.com/vi/4YrnS2aaSkw/0.jpg)](http://www.youtube.com/watch?v=4YrnS2aaSkw "LCD Display and Navigation")

### Mixer Panel and Controls ###

[![](http://img.youtube.com/vi/BjKG9kKLDo0/0.jpg)](http://www.youtube.com/watch?v=BjKG9kKLDo0 "Mixer Panel and Controls")

### Controlling Arturia Plugins with Analog Lab ###

[![](http://img.youtube.com/vi/QtMN1y-Kf_w/0.jpg)](http://www.youtube.com/watch?v=QtMN1y-Kf_w "Analog Lab Mode")

### Controlling Other Plugins and Learning Midi Assignments ###

[![](http://img.youtube.com/vi/4nkRHf5kwT8/0.jpg)](http://www.youtube.com/watch?v=4nkRHf5kwT8 "Controlling plugins")

### Remapping the Pads ###

[![](http://img.youtube.com/vi/wiynzuc7Vqg/0.jpg)](http://www.youtube.com/watch?v=wiynzuc7Vqg "Remapping Pad Buttons")

### DAW controls and Transports ###

[![](http://img.youtube.com/vi/hSm6koiTwVA/0.jpg)](http://www.youtube.com/watch?v=hSm6koiTwVA "DAW controls and transports")

