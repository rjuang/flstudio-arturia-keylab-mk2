import arrangement
import arturia_leds
import arturia_midi
import channels
import general
import midi
import patterns
import time
import transport
import ui

from arturia_display import ArturiaDisplay
from arturia_encoders import ArturiaInputControls
from arturia_leds import ArturiaLights
from arturia_metronome import VisualMetronome
from arturia_pages import ArturiaPagedDisplay
from arturia_scheduler import Scheduler

SCRIPT_VERSION = general.getVersion()

# Enable support for FL Studio 20.7.2  (Version 7) by avoiding new APIs
if SCRIPT_VERSION >= 8:
  import plugins


class ArturiaController:
    """Controller responsible for managing all the different components in a single class. """
    def __init__(self):
        self._scheduler = Scheduler()
        self._display = ArturiaDisplay(self._scheduler)
        self._paged_display = ArturiaPagedDisplay(self._display, self._scheduler)
        self._lights = ArturiaLights()
        self._metronome = VisualMetronome(self._lights)
        self._encoders = ArturiaInputControls(self._paged_display, self._lights)
        self._last_send = 0
        self._send_interscript_idle = True

    def display(self):
        return self._display

    def lights(self):
        return self._lights

    def metronome(self):
        return self._metronome

    def paged_display(self):
        return self._paged_display

    def encoders(self):
        return self._encoders

    def scheduler(self):
        return self._scheduler

    def Sync(self, flags):
        """ Syncs up all visual indicators on keyboard with changes from FL Studio. """
        # Update buttons
        if flags & midi.HW_Dirty_LEDs:
            led_map = {
                ArturiaLights.ID_TRANSPORTS_RECORD: ArturiaLights.AsOnOffByte(transport.isRecording()),
                ArturiaLights.ID_TRANSPORTS_LOOP: ArturiaLights.AsOnOffByte(ui.isLoopRecEnabled()),
                ArturiaLights.ID_GLOBAL_METRO: ArturiaLights.AsOnOffByte(ui.isMetronomeEnabled()),
                ArturiaLights.ID_GLOBAL_SAVE: ArturiaLights.AsOnOffByte(transport.getLoopMode() == 1),
                ArturiaLights.ID_GLOBAL_UNDO: ArturiaLights.AsOnOffByte(general.getUndoHistoryLast() == 0),
                ArturiaLights.ID_TRACK_SOLO: ArturiaLights.AsOnOffByte(
                    channels.isChannelSolo(channels.selectedChannel())),
                ArturiaLights.ID_TRACK_MUTE: ArturiaLights.AsOnOffByte(
                    channels.isChannelMuted(channels.selectedChannel())),
                ArturiaLights.ID_TRANSPORTS_STOP: ArturiaLights.AsOnOffByte(not transport.isPlaying()),
                ArturiaLights.ID_TRANSPORTS_PLAY: ArturiaLights.AsOnOffByte(transport.getSongPos() > 0),
                ArturiaLights.ID_GLOBAL_OUT: ArturiaLights.AsOnOffByte(
                    arrangement.selectionEnd() > arrangement.selectionStart()),
                ArturiaLights.ID_NAVIGATION_LEFT: ArturiaLights.AsOnOffByte(ui.getVisible(midi.widChannelRack)),
                ArturiaLights.ID_NAVIGATION_RIGHT: ArturiaLights.AsOnOffByte(ui.getVisible(midi.widMixer)),
                ArturiaLights.ID_OCTAVE_PLUS: ArturiaLights.LED_OFF,
                ArturiaLights.ID_OCTAVE_MINUS: ArturiaLights.LED_OFF,
            }
            self._lights.SetLights(led_map)
            self._encoders.Refresh()

        # Update display
        channel_name = channels.getChannelName(channels.selectedChannel())
        pattern_number = patterns.patternNumber()
        pattern_name = patterns.getPatternName(pattern_number)
        update = (flags & (1024     # HW_Dirty_Patterns
                           | 2048   # HW_Dirty_Tracks
                           | 16384  # HW_Dirty_Names
                           | 32     # HW_Dirty_FocusedWindow   (channel selection)
                           )
                  ) > 0
        self._paged_display.SetPageLines(
            'main',
            line1='[%d:%d] %s' % (channels.selectedChannel() + 1, pattern_number, channel_name),
            line2='%s' % pattern_name,
            update=update)

    def _TurnOffOctaveLights(self):
        # Disable blinking lights on octave keyboard
        if time.time() - self._last_send >= 0.5:
            self._lights.SetLights({
                ArturiaLights.ID_OCTAVE_PLUS: ArturiaLights.LED_OFF,
                ArturiaLights.ID_OCTAVE_MINUS: ArturiaLights.LED_OFF,
            })
            self._last_send = time.time()

    def RefreshDisplay(self):
        self._paged_display.Refresh()

    def DisableInterscriptIdle(self):
        self._send_interscript_idle = False

    def Idle(self):
        self._scheduler.Idle()
        if self._send_interscript_idle:
            arturia_midi.dispatch_message_to_other_scripts(
                arturia_midi.INTER_SCRIPT_STATUS_BYTE,
                arturia_midi.INTER_SCRIPT_DATA1_IDLE_CMD,
                0)

        if arturia_leds.ESSENTIAL_KEYBOARD:
            self._TurnOffOctaveLights()
