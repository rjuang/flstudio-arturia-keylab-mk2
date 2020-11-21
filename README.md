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
- Punch in button -- press this to set a begin selection marker. Light turns on when a start selection marker has been 
set.
- Punch out button -- press this to set the end selection marker. Light turns on when pressing this results in a
selected range. Pressing this button a second time will unselect the selected range and also turn off the light.
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

#### Navigation Panel
- The left and right arrows will cycle through various modes. These are:
  1. Volume - turning the knob will set the active channel volume.
  2. Panning - turning the knob will set the active channel panning.
  3. Pitch - turning the knob will set the active channel pitch.
  4. Time Marker - turning the knob will advance/retreat the time marker by 1 beat.
  5. Pattern - turning the knob will select the active pattern.
  6. Channel - turning the knob will select the active channel.
  7. Plugin Preset - when a channel with a plugin is selected, turning the knob will display the window and cycle
   through the presets. I've tested this only on FLEX plugin and it works for cycling through the different presets.
  8. Color (Red, Green, Blue) - Set the color of the active channel with the knob.
- The knob initially controls the active channel's volume. Pressing left/right will switch through what the knob
 controls.
- The display will momentarily update with the value before going back to the default display.

### Encoder Knobs
- Encoder knobs will allow setting values for the actively selected channel in the channel rack. The goal is to allow
the encoder knobs to tweak plugin parameters directly from the MIDI controller and not require computer interaction.
  - Model workflow: The user selects a channel they want to edit.
  - They tweak the knobs or press the 'Next' button to cycle through the different knob mappings.
  - Once they are done, they can continue tweaking knobs live while playing or switch to a different channel
  - The knob mappings will update to the correct mapping when switching between channels with different plugins. 
  
- Currently, only FLEX plugin has been mapped out. All knobs and sliders are accessible from one of the knob pages.
- The knobs will currently control plugin sliders/knobs and tries its best to pull any data from the plugin into the
 display.
- Pressing the Next button (with bank button light off) will result in cycling through the different knob pages. The
 display will update to show what page number and the PAD lights will also light up to show what page number it is
 mapping the knobs to. Note: The top 2 rows of the 4x4 pad-lights correspond to the knobs. The bottom 2 rows of the 4x4
 pad lights correspond to the sliders. Currently, I haven't mapped the sliders yet.
- When the knobs are turned, it will pull the hint displayed to FL Studio, abbreviate any known words and display them
on the MIDI device display along with the updated value. This only works with FLEX currently. Also to note, some plugins
(e.g. Analog Lab 4) don't seem to provide any hint text to FL Studio.
- FLEX plugins have 6 pages mapped out and correspond to groupings of buttons.

## Remaining Work To Do
- Map other plugins.
- Figure out what to use the encoder knobs and sliders for.
- Figure out how to add a new instrument to the channel rack
 -Figure out how to have sliders/knobs tweak the plugin page.

