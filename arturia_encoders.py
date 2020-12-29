import channels
import general
import midi
import mixer
import transport
import ui

from arturia_display import ArturiaDisplay
from arturia_leds import ArturiaLights
from debug import log

class ArturiaInputControls:
    """ Manges what the sliders/knobs control on an Arturia Keyboard.

     On the Arturia KeyLab 61 Keyboard, there is a row of 9 encoders and 9 sliders. Plugins may have
     more than 9 encoders/sliders. As such, we will allow mapping the Next/Previous buttons to
     different "pages".
     """
    INPUT_MODE_CHANNEL_PLUGINS = 0
    INPUT_MODE_MIXER_OVERVIEW = 1
    MODE_NAMES = {
        INPUT_MODE_CHANNEL_PLUGINS: 'Channel Plugin',
        INPUT_MODE_MIXER_OVERVIEW: 'Mixer Panel',
    }
    NUM_INPUT_MODES = 2

    @staticmethod
    def _to_rec_value(value, limit=midi.FromMIDI_Max):
        return int((value / 127.0) * limit)

    @staticmethod
    def _set_plugin_param(param_id, value, incremental=False):
        event_id = channels.getRecEventId(channels.selectedChannel()) + midi.REC_Chan_Plugin_First + param_id
        if incremental:
            value = channels.incEventValue(event_id, value, 0.01)
        else:
            value = ArturiaInputControls._to_rec_value(value, limit=65536)
        general.processRECEvent(
            event_id, value, midi.REC_UpdateValue | midi.REC_UpdatePlugLabel | midi.REC_ShowHint
                             | midi.REC_UpdateControl | midi.REC_SetChanged)

    @staticmethod
    def _set_mixer_param(param_id, value, incremental=False, track_index=0, plugin_index=0):
        event_id = mixer.getTrackPluginId(track_index, plugin_index) + param_id
        if incremental:
            value = channels.incEventValue(event_id, value, 0.01)
        else:
            value = ArturiaInputControls._to_rec_value(value, limit=16384)

        general.processRECEvent(
            event_id, value, midi.REC_UpdateValue | midi.REC_UpdatePlugLabel | midi.REC_ShowHint
                             | midi.REC_UpdateControl | midi.REC_SetChanged)

    @staticmethod
    def _set_mixer_param_fn(param_id, incremental=False, track_index=0, plugin_index=0):
        return lambda v: ArturiaInputControls._set_mixer_param(
            param_id, v, incremental=incremental, track_index=track_index, plugin_index=plugin_index)

    @staticmethod
    def _set_plugin_param_fn(param_id, incremental=False):
        return lambda v: ArturiaInputControls._set_plugin_param(param_id, v, incremental=incremental)

    @staticmethod
    def _plugin_map_for(offsets, incremental=False):
        return [ArturiaInputControls._set_plugin_param_fn(x, incremental=incremental) for x in offsets]

    @staticmethod
    def _mixer_map_for(param_id, track_indices, incremental=False):
        return [ArturiaInputControls._set_mixer_param_fn(param_id, track_index=t, incremental=incremental)
                for t in track_indices]

    def __init__(self, paged_display, lights):
        self._paged_display = paged_display
        self._lights = lights
        self._current_mode = ArturiaInputControls.INPUT_MODE_MIXER_OVERVIEW

        # Maps a string containing the input control mode to another dictionary containing a mapping of
        # the plugin names to an array of lambda functions to execute for the corresponding offset.
        self._knobs_map = {}
        self._sliders_map = {}

        self._knobs_map[ArturiaInputControls.INPUT_MODE_CHANNEL_PLUGINS] = {
            # Default mapping. Sequential. Good for debugging
            '': [
                self._plugin_map_for(range(0, 9), incremental=True),
                self._plugin_map_for(range(9, 18), incremental=True),
                self._plugin_map_for(range(18, 27), incremental=True),
                self._plugin_map_for(range(27, 36), incremental=True),
                self._plugin_map_for(range(36, 45), incremental=True),
                self._plugin_map_for(range(45, 54), incremental=True),
                self._plugin_map_for(range(54, 63), incremental=True),
                self._plugin_map_for(range(63, 72), incremental=True),
            ],

            # Mapping for FLEX plugin
            'FLEX': [
                # Note: Sliders associated with FLEX plugin are in the sliders map
                # Filter knobs, Filter Env AHDSR
                self._plugin_map_for([18, 20, 19, 5, 6, 7, 8, 9, 39], incremental=True),
                # Master knobs + type,  Volume Env AHDSR, Master ON/OFF
                self._plugin_map_for([21, 22, 23, 0, 1, 2, 3, 4, 40], incremental=True),
                # Delay buttons
                self._plugin_map_for([25, 26, 27, 29, 28, 24, 37, 37, 37], incremental=True),
                # Reverb buttons
                self._plugin_map_for([30, 31, 32, 34, 33, 44, 38, 38, 38], incremental=True),
                # Limiter
                self._plugin_map_for([35, 42, 43, 41, 41, 41, 41, 41, 41], incremental=True),
            ],
        }

        self._sliders_map[ArturiaInputControls.INPUT_MODE_CHANNEL_PLUGINS] = {
            '': [
                self._plugin_map_for(range(0, 9)),
                self._plugin_map_for(range(9, 18)),
                self._plugin_map_for(range(18, 27)),
                self._plugin_map_for(range(27, 36)),
                self._plugin_map_for(range(36, 45)),
                self._plugin_map_for(range(45, 54)),
                self._plugin_map_for(range(54, 63)),
                self._plugin_map_for(range(63, 72)),
            ],
            # Mapping for FLEX plugin
            'FLEX': [
                # Sliders 1-8, Output Volume
                self._plugin_map_for([10, 11, 12, 13, 14, 15, 16, 17, 36]),
            ],
        }

        self._sliders_map[ArturiaInputControls.INPUT_MODE_MIXER_OVERVIEW] = {
            '': [self._mixer_map_for(midi.REC_Mixer_Vol, [1, 2, 3, 4, 5, 6, 7, 8, 0])],
        }

        self._knobs_map[ArturiaInputControls.INPUT_MODE_MIXER_OVERVIEW] = {
            '': [
                self._mixer_map_for(midi.REC_Mixer_Pan, [1, 2, 3, 4, 5, 6, 7, 8, 0], incremental=True),
                self._mixer_map_for(midi.REC_Mixer_SS, [9, 10, 11, 4, 5, 6, 7, 8, 0], incremental=True),
            ],
        }

        self._pending_slider_requests = {}
        self._knobs_mode = ''
        self._knobs_mode_index = 0
        self._sliders_mode = ''
        self._sliders_mode_index = 0
        self._last_unknown_knob_mode = ''
        self._last_unknown_slider_mode = ''
        self._last_hint_title = ''
        self._last_hint_value = ''
        self._last_hint_time_ms = 0

    def SetKnobs(self, base_fn=None, offset=None):
        if base_fn is not None:
            self._knobs_base_fn = base_fn
        if offset is not None:
            self._knobs_offset = offset
        return self

    def SetSliders(self, base_fn=None, offset=None):
        if base_fn is not None:
            self._sliders_base_fn = base_fn
        if offset is not None:
            self._sliders_offset = offset
        return self

    def SetKnobMode(self, knob_mode):
        if knob_mode not in self._knobs_map[self._current_mode]:
            self._last_unknown_knob_mode = knob_mode
            log('WARNING', 'No encoder mapping for plugin <%s>' % knob_mode)
            knob_mode = ''
        else:
            self._last_unknown_knob_mode = ''
        self._knobs_mode = knob_mode
        self._knobs_mode_index = 0
        return self

    def SetSliderMode(self, slider_mode):
        if slider_mode not in self._sliders_map[self._current_mode]:
            self._last_unknown_slider_mode = slider_mode
            log('WARNING', 'No encoder mapping for plugin <%s>' % slider_mode)
            slider_mode = ''
        else:
            self._last_unknown_slider_mode = ''
        self._sliders_mode = slider_mode
        self._sliders_mode_index = 0
        return self

    def SetCurrentMode(self, mode):
        self._current_mode = mode
        self._display_hint('Controlling', ArturiaInputControls.MODE_NAMES[mode])
        self._update_lights()

    def GetCurrentMode(self):
        return self._current_mode

    def _get_knob_pages(self):
        knob_key = self._knobs_mode
        if knob_key not in self._knobs_map[self._current_mode]:
            knob_key = ''
        return self._knobs_map[self._current_mode][knob_key]

    def _get_slider_pages(self):
        sliders_key = self._sliders_mode
        if sliders_key not in self._sliders_map[self._current_mode]:
            sliders_key = ''
        return self._sliders_map[self._current_mode][sliders_key]

    def NextKnobsPage(self):
        num_pages = len(self._get_knob_pages())
        if num_pages == 0:
            return
        self._knobs_mode_index = (self._knobs_mode_index + 1) % num_pages
        self._update_lights()
        self._display_hint(' Knobs Mapping', '     %d of %d' % (self._knobs_mode_index + 1, num_pages))
        return self

    def NextSlidersPage(self):
        num_pages = len(self._get_slider_pages())
        if num_pages == 0:
            return
        self._sliders_mode_index = (self._sliders_mode_index + 1) % num_pages
        self._update_lights()
        self._display_hint(' Sliders Mapping', '     %d of %d' % (self._sliders_mode_index + 1, num_pages))
        return self

    def ProcessKnobInput(self, knob_index, delta):
        pages = self._get_knob_pages()
        if len(pages) == 0:
            # Knob mode is invalid
            self._display_unset_knob()
            return

        # Assume index is always valid
        knobs = pages[self._knobs_mode_index]

        # Check if knob is mapped
        if knob_index >= len(knobs):
            # Knob is unmapped in the array
            self._display_unset_knob()
            return

        knobs[knob_index](delta)
        self._check_and_show_hint()
        return self

    def ProcessSliderInput(self, slider_index, value):
        pages = self._get_slider_pages()
        if len(pages) == 0:
            # Slider mode is invalid
            self._display_unset_slider()
            return

        # Assume index is always valid
        sliders = pages[self._sliders_mode_index]

        # Check if knob is mapped
        if slider_index >= len(sliders):
            # Slider is unmapped in the array
            self._display_unset_slider()
            return
        sliders[slider_index](value)
        return self

    def StartOrEndSliderInput(self):
        self._check_and_show_hint()

    def Refresh(self):
        # Don't update lights if recording
        if not transport.isRecording() and not transport.isPlaying():
            self._update_lights()

    def _display_hint(self, hint_title, hint_value):
        hint_title = ArturiaDisplay.abbreviate(hint_title.upper())
        hint_value = hint_value.upper()

        if self._last_hint_title != hint_title:
            self._paged_display.display().ResetScroll()

        self._last_hint_title = hint_title
        self._last_hint_value = hint_value
        self._paged_display.SetPageLines('hint', line1=hint_title, line2=hint_value)
        current_time_ms = ArturiaDisplay.time_ms()

        if current_time_ms > self._last_hint_time_ms + 100:
            self._paged_display.SetActivePage('hint', expires=5000)
            self._last_hint_time_ms = current_time_ms

    def _display_unset_slider(self):
        self._display_hint(' (SLIDER UNSET) ', ' ')

    def _display_unset_knob(self):
        self._display_hint(' (KNOB UNSET) ', ' ')

    def _check_and_show_hint(self):
        hint = ui.getHintMsg()
        if not hint:
            return

        lines = hint.split(':', 1)
        if len(lines) == 1:
            lines.append(' ')
        self._display_hint(lines[0], lines[1][:16])

    def _get_pad_position(self, index):
        return int(index / 4) % 2, index % 4

    def _update_lights(self):
        # Set 4x4 Pad lights to indicate the current configuration
        pad_values = ArturiaLights.Zero4x4Matrix()

        knob_row, knob_col = self._get_pad_position(self._knobs_mode_index)
        slider_row, slider_col = self._get_pad_position(self._sliders_mode_index)
        pad_values[knob_row][knob_col] = ArturiaLights.LED_ON
        pad_values[slider_row + 2][slider_col] = ArturiaLights.LED_ON
        self._lights.SetPadLights(pad_values)

        is_channel_mode = self._current_mode == ArturiaInputControls.INPUT_MODE_CHANNEL_PLUGINS
        is_mixer_mode = self._current_mode == ArturiaInputControls.INPUT_MODE_MIXER_OVERVIEW

        self._lights.SetLights({
            ArturiaLights.ID_BANK_NEXT: ArturiaLights.AsOnOffByte(is_channel_mode),
            ArturiaLights.ID_BANK_PREVIOUS: ArturiaLights.AsOnOffByte(is_mixer_mode),
        })
