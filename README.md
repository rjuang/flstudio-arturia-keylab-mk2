# MIDI Script for Arturia Keylab 49/61/88 mkII

## Overview
The goal of this MIDI Script is to make Arturia Keylab mkII more friendlier to use with FL Studio.

## Demo (updated video, some changes to default start since recording)
[![](http://img.youtube.com/vi/Ts2SnW9r2fc/0.jpg)](http://www.youtube.com/watch?v=Ts2SnW9r2fc "Updated Demo of Script")

## Discussion Thread
There is a discussion thread you can provide feedback or ask questions at [here](https://forum.image-line.com/viewtopic.php?f=1994&t=243170)

## Discord Server
I can also be reached via [Discord](https://discord.gg/FS7sjmmh)


## Setting Up
Video link describing setup below:

[![](http://img.youtube.com/vi/TXZ3u1srTmw/0.jpg)](http://www.youtube.com/watch?v=TXZ3u1srTmw "Video showing how to install script into FL Studio")

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

## What's Done

### DAW Commands/User panel 

Buttons in the DAW Commands/User section are mapped as follows:

| Solo        |   Mute       |  New Pattern  (HOLD=Clone pattern) | Prev. Pattern  | Next Pattern|
|-------------|--------------|------------------------------------|----------------|-------------|
| Song Mode   |  Punch In    |  Punch Out                         |  Metro         | Undo        |

Where the first row is the buttons under TRACK CONTROLS and the second row are buttons under
GLOBAL CONTROLS.

#### Track Controls (actually Channel/Pattern Controls)
- Solo will solo the active channel selected in FL Studio's channel rack. The Solo LED will turn on
 if the channel is set to solo.
- Mute will mute the active channel selected in FL Studio's channel rack. The Mute LED will turn on
 if the channel is muted.
- New Pattern will create a new pattern with a generic name, select it, and make it the active
 pattern. If this button is held down for a long press, then it will clone the active pattern instead and select
 the cloned pattern.
- Pressing "New pattern" when a punch in/punch out selection has been made will create a new pattern with the 
selection pasted in.
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
- Long pressing UNDO will clear the active channel's pattern.

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
- The Next button will cycle through different "pages" for knobs.
- The Prev button will cycle through different "pages" for sliders.
- Press and hold the Next button to set the sliders/knobs to control channel plugin.
- Press and hold the Prev button to set the sliders/knobs to control the mixer panel.
- Make sure bank light button is off. If it is on, then you will need to press the Bank button to toggle it off. When
 the bank light button is lit, the Next/Prev buttons will switch between the channel plugin and mixer panel modes
 (i.e. same as long pressing Next/Prev when bank light button is off).

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

### Encoder Knobs and Sliders
- Sliders and encoders will control either the mixer panel or the active channel plugin parameters.
- If the "Part 1 / Next" light is glowing, then it is controlling the channel plugin.
- If the "Part 2 / Prev" light is glowing, then it is controlling the mixer levels in the mixer panel.
- Currently, when starting up, the "Part 2 / Prev" light will be selected and the sliders/knobs will control the
 mixer levels in the mixer panel. Long press the Part 1 / Part 2 buttons to switch what the encoder knobs/sliders
  control.
- When controlling the channel plugin, encoder knobs will allow setting values for the actively selected channel in the
 channel rack. The goal is to allow the encoder knobs to tweak plugin parameters directly from the MIDI controller and
 not require computer interaction.
  - Model workflow: The user selects a channel they want to edit.
  - They tweak the knobs/sliders or press the 'Next' button to cycle through the different knob mappings.
  - They can cycle through the sliders by pressing the 'Prev' button.
  - Once they are done, they can continue tweaking knobs live while playing or switch to a different channel
  - The knob mappings will update to the correct mapping when switching between channels with different plugins. 
  
- Currently, only FLEX plugin has been mapped out. All knobs are mapped to the encoder knobs. All sliders (except the
 pitch) are mapped tot the sliders.
- The knobs will currently control plugin knobs and tries its best to pull any data from the plugin into the
 display.
- The sliders will control sliders in the plugin and also try its best to pull any data from the plugin into the
 display.
- Pressing the Next button (with bank button light off) will result in cycling through the different knob pages. The
 display will update to show what page number and the PAD lights will also light up to show what page number it is
 mapping the knobs to. Note: The top 2 rows of the 4x4 pad-lights correspond to the knobs. The bottom 2 rows of the 4x4
 pad lights correspond to the sliders. Currently, I haven't mapped the sliders yet.
- Pressing the Prev button (with bank button light off) will result in cycling through the different slider pages. The
 display will update to show what page number and the PAD lights will also light up to show what page number it is 
 mapping the sliders to.
- When the knobs are turned (or sliders moved), it will pull the hint displayed to FL Studio, abbreviate any known words
 and display them on the MIDI device display along with the updated value. This only works with FLEX currently. Also to
  note, some plugins (e.g. Analog Lab 4) don't seem to provide any hint text to FL Studio.
- FLEX plugins have 5 pages mapped out, with each page corresponding to a grouping of buttons that make sense. There is
only one page of sliders. Only the pitch slider is mapped to a knob.

## Programmable Pads
- You can record sequences from any channels into a pad button (and yes, you can even switch channels and record
 multiple key presses into a pad!)
- To put a drum pad into recording mode, hold it for 1 second until it starts blinking.
- Switch to any channel you desire. Press a key on the keyboard or sequence of keys. You are welcome to change channels
as fast as you can. The initial and ending silence are ignored.
- To exit recording mode, press any drum key.
- Note: the programmed customizations do get saved to the current project. Because FL Studio midi script API restricts 
disk access from midi script, I'm forced to embed the mapping in the name of a mixer track. You will see the very far 
left mixer (denoted by the letter "C") have a strange name with the string "DO NOT EDIT".
- Looping: To put a drum pad playback in an infinite loop, hold down the sustain pedal (you will need to have a sustain pedal
attached) and then press the drum pad key. You can release the sustain pedal. It will keep looping the pattern. You
can stop the loop by pressing the drum pad again. It will finish the current sequence before halting playback.

## Remaining Work To Do
- Map other plugins.
- Figure out how to add a new instrument to the channel rack
- Figure out if there's a way to manually label the params and display the believed value (or retrieve one).
- Figure out how to detect when bank button is pressed (maybe retrieve the midi led status of the light on refresh ?)
- A HOWTO page and video snippets on doing different things to showcase the different features.

## Known Issues
- When creating a new pattern when a punch-in/punch-out selection exists, the result seems to be shifted by 1 bar.
This seems to be a bug in FL Studio. Try copying a selection from a pattern and pasting it into a new pattern.

## Planned TODOs:
- Fix mod/pitch wheel mapping.
- Hold down "Solo" button to switch bank mapping buttons to toggle solo for mixer/channel track 1 - 8 (
depending if active mixer mode or channel mode)
- Hold down "Mute" button to switch bank mapping buttons to toggle mute for mixer/channel track 1 - 8 (
depending if active mixer mode or channel mode)
- Hold down "Record" button to switch bank mapping buttons to toggle arm "disk" recording for track 1 - 8 

## Ideas to consider
Some ideas I came up with that would help with my workflow. Will consider adding this at some point:

- Replace color red/green/blue entries with a single color scroller with simple presets of 4*4*4 colors where we permute
  R=range(0,255, 256/4), G=range(0,255, 256/4), and B=range(0,255, 256/4)
- Holding down the left/right navigation buttons will cycle through bank select modes
  - Bank select mode:
    - default channel selection (so you can quickly pick instruments to play)
    - ability to cycle through mixer mute, recordd arm
- Long press navigation knob to switch knob functionality between:
  - left/right, up/down, modes (volume, panning, etc)
- Pressing knob key sends F8 key and switches controls to left/right/up/down navigation... missing enter key here, 
 so might not be useful to entertain this idea.
- Long pressing pad keys triggers recording a local pattern for that key to midiscript until that key is pressed again.
 Pressing the keypad to trigger the saved snippet pattern. Thoughts: this will make long pressing pad keys for playing
 impossible. Does anyone actually press and hold the drump pad keys ?
 


