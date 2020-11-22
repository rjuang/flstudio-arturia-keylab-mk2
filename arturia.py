import arrangement
import channels
import debug
import general
import patterns
import plugins
import transport
import ui

from arturia_display import ArturiaDisplay
from arturia_encoders import ArturiaInputControls
from arturia_leds import ArturiaLights
from arturia_metronome import VisualMetronome
from arturia_pages import ArturiaPagedDisplay


class ArturiaController:
    """Controller responsible for managing all the different components in a single class. """
    def __init__(self):
        self._display = ArturiaDisplay()
        self._paged_display = ArturiaPagedDisplay(self._display)
        self._lights = ArturiaLights()
        self._metronome = VisualMetronome(self._lights)
        self._encoders = ArturiaInputControls(self._paged_display, self._lights)

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

    def Sync(self):
        """ Syncs up all visual indicators on keyboard with changes from FL Studio. """
        # Update buttons
        active_index = channels.selectedChannel()
        led_map = {
            ArturiaLights.ID_TRANSPORTS_RECORD: ArturiaLights.AsOnOffByte(transport.isRecording()),
            ArturiaLights.ID_TRANSPORTS_LOOP: ArturiaLights.AsOnOffByte(ui.isLoopRecEnabled()),
            ArturiaLights.ID_GLOBAL_METRO: ArturiaLights.AsOnOffByte(ui.isMetronomeEnabled()),
            ArturiaLights.ID_GLOBAL_SAVE: ArturiaLights.AsOnOffByte(transport.getLoopMode() == 1),
            ArturiaLights.ID_GLOBAL_UNDO: ArturiaLights.AsOnOffByte(general.getUndoHistoryLast() == 0),
            ArturiaLights.ID_TRACK_SOLO: ArturiaLights.AsOnOffByte(channels.isChannelSolo(active_index)),
            ArturiaLights.ID_TRACK_MUTE: ArturiaLights.AsOnOffByte(channels.isChannelMuted(active_index)),
            ArturiaLights.ID_TRANSPORTS_STOP: ArturiaLights.AsOnOffByte(not transport.isPlaying()),
            ArturiaLights.ID_TRANSPORTS_PLAY: ArturiaLights.AsOnOffByte(transport.getSongPos() > 0),
            ArturiaLights.ID_GLOBAL_OUT: ArturiaLights.AsOnOffByte(
                arrangement.selectionEnd() > arrangement.selectionStart()),
        }
        self._lights.SetLights(led_map)

        # Update selected channel
        bank_lights = [ArturiaLights.LED_OFF] * 9
        if active_index < len(bank_lights):
            bank_lights[active_index] = ArturiaLights.LED_ON
        self._lights.SetBankLights(bank_lights)

        # Update display
        channel_name = channels.getChannelName(active_index)
        pattern_number = patterns.patternNumber()
        pattern_name = patterns.getPatternName(pattern_number)

        # Update knob mode
        plugin_name = plugins.getPluginName(active_index) if plugins.isValid(active_index) else ''
        self._encoders.SetKnobMode(plugin_name)
        self._encoders.SetSliderMode(plugin_name)

        self._paged_display.SetPageLines(
            'main',
            line1='[%d:%d] %s' % (active_index + 1, pattern_number, channel_name),
            line2='%s' % pattern_name)
        self._encoders.Refresh()