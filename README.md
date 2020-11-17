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

### DAW Commands/User panel 

Buttons in the DAW Commands/User section are mapped as follows:

| Solo        |   Mute       |  New Pattern  | Prev. Pattern  | Next Pattern|
|-------------|--------------|---------------|----------------|-------------|
| Song Mode   |  Punch In    |  Punch Out    |  Metro         | Undo        |

Where the first row is the buttons under TRACK CONTROLS and the second row are buttons under
GLOBAL CONTROLS.

#### Track Controls (actually Channel/Pattern Controls)
- Solo will solo the active channel selected in FL Studio's channel rack. The Solo LED will turn on
 if the channel is set to solo.
- Mute will mute the active channel selected in FL Studio's channel rack. The Mute LED will turn on
 if the channel is muted.
- New Pattern will create a new pattern with a generic name, select it, and make it the active
 pattern.
- Prev. Pattern will move up the pattern list and select the previous pattern and make it active. This
 button has no effect if there is no previous pattern.
- Next Pattern will move down the pattern list and select the next pattern and make it active. This
 button has no effect if there is no next pattern. You must use "New Pattern" to create a new pattern.
- The Display will be updated whenever patterns/channel changes. It will display:
```
[C:P] Channel Name
Pattern Name
```
 - Where C is the channel number and P is the pattern number. The display will show the line as a marquee
  scrolling display if it doesn't fit within 16 chars.

#### Global Controls
- Song mode button will light up if FL Studio is in Song playback mode. Pressing the button will toggle
 between song and pattern playback. The LED is on when playback mode is Song.
- Punch in button -- I have this linked to FL Studio's punch in handler. I haven no idea if it's 
implemented correctly. I haven't figured out what punch in function is.
- Punch out button -- I have this linked to FL Studio's punch out handler. I have no idea if it's
implemented correctly. I haven't figureed out what the punch out function is.
- Metro toggles the metronome. The LED lights up if the Metronome is enabled. Note that there is a 
visual metronome that will light up the 4x4 grid lights as well as the rewind/forward transport 
buttons on the keyboard.
- Undo button will only undo at most one step. If pressed a second time, it will redo the step
 (cancelling the undo). The undo LED lights up if there is an action to Undo. It is off if the action
 is already undone. When OFF, pressing the UNDO button will act as a REDO.

#### Transports Buttons
- The transports buttons is fully implemented.
- Pressing and holding the rewind button will move the time marker backwards.
 Letting go will halt the rewind.
- Pressing and holding the forward button will move the time marker forwards.
 Letting go will halt the forward.
- Stop button will stop the song and set the time marker to the beginning. The button is lit when the song
  is stopped or paused.
- Play/pause button will toggle between playing and pausing the song. If the song is paused,
 both the play/pause button and stop button will be lit.
- Record button will arm the track for recording. The button will be ON if Recording armed.
- Loop button will enable loop recording. The button will be lit if loop recording is enabled.

#### Visual Metronome
- When a song/pattern is playing, the 4x4 grid will sequentially light up to serve as a visual metronome.
The rows serve as a 4-count beat visual metronome. We also alternate lighting up the rewind and fast
 forward buttons in the Transports button group. This serves as a 2-count beat visual metronome.

#### Channel Select Buttons
- The Select buttons under the sliders will select channels 1-8 in the channel rack. 
- I've yet to tie in the Next/Previous buttons for enabling channel selections above 8. 
- No idea what to do with the Part 1/Part 2 buttons when the Live button is on.


## Remaining Work To Do
- Figure out if I want to keep the punch in/out buttons and if they are useful.
- Figure out how to make the navigation knob and knob press and buttons useful. 
Thinking of something to toggle modes for adjusting pan/volume, etc.
- Figure out what to use the encoder knobs and sliders for.
- I'd like to do something with arrangements flow for this, but still thinking of what will be useful.

