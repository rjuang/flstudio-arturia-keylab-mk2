# MIDI Script for Arturia Keylab 49/61/88 mkII

## Overview
The goal of this MIDI Script is to make Arturia Keylab mkII more friendlier to use with FL Studio.


## Setting Up
You can simply clone this project into the folder:
``` 
Documents/Image-Line/FL Studio/Settings/Hardware/
```
Then in FL Studio, goto `Options->Midi Settings` and select your Arturia device (the DAW one) under
`Input` section. Click the `Controller type` drop down and select `Arturia Keylab mkII`.


## What's Done

- Currently reverse engineered the MIDI protocols for sliders, LEDs, display, encoders and buttons.
- When DAW mode selected on keyboard, all transports buttons work.
- Selecting a bank/select key will select the corresponding instrument in the channel rack. It will also
update the display to show the name of the channel, the pan and volume levels. If the text exceeds 16-chars,
it will scroll the text repeatedly.
- The track solo and mute buttons work to properly solo and mute the active track. LEDs will properly
 light up when solo/mute.
- Setup basic framework for setting multiple LEDs.
- Setup basic syncing between FL Studio UI state and keyboard. 
- Save button corresponds to toggling Pattern/Song playback mode. Glowing LED means Song mode.

