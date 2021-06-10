import channels
import general
import midi
import mixer
import transport
import ui

from arturia_display import ArturiaDisplay
from arturia_leds import ArturiaLights
from debug import log

SCRIPT_VERSION = general.getVersion()

if SCRIPT_VERSION >= 8:
    import plugins


def _auto_generate_knobs_mapping(plugin_idx):
    if SCRIPT_VERSION < 8:
        return False
    params = _get_param_names(plugin_idx)
    map_idx = [
        _find_parameter_index(params, 'cutoff', 'filter', '1'),
        _find_parameter_index(params, 'resonance', 'filter', '1'),
        _find_parameter_index(params, 'lfo', 'delay', '1'),
        _find_parameter_index(params, 'lfo', 'rate', '1'),
        _find_parameter_index(params, 'macro', '1'),
        _find_parameter_index(params, 'macro', '2'),
        _find_parameter_index(params, 'macro', '3'),
        _find_parameter_index(params, 'macro', '4'),
        _find_parameter_index(params, 'chorus'),
    ]
    for idx in map_idx:
        if idx >= 0:
            return map_idx
    return []


def _get_param_names(plugin_idx):
    return [plugins.getParamName(i, plugin_idx).lower() for i in range(plugins.getParamCount(plugin_idx))]


def _find_parameter_index(parameter_names, *keywords):
    candidates = set(enumerate(parameter_names))
    for keyword in keywords:
        keyword = keyword.lower()
        if len(candidates) <= 1:
            break
        next_candidates = []
        for val in candidates:
            if keyword in val[1]:
                next_candidates.append(val)
        candidates = next_candidates
    return candidates[0][0] if candidates else -1


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

    def _set_plugin_param(self, param_id, value, incremental=False):
        if param_id < 0:
            # Ignore negative values
            self._display_unset()
            return
        plugin_idx = channels.selectedChannel()
        event_id = channels.getRecEventId(plugin_idx) + midi.REC_Chan_Plugin_First + param_id
        if incremental:
            value = channels.incEventValue(event_id, value, 0.01)
        else:
            value = ArturiaInputControls._to_rec_value(value, limit=65536)
        general.processRECEvent(
            event_id, value, midi.REC_UpdateValue | midi.REC_UpdatePlugLabel | midi.REC_ShowHint
                             | midi.REC_UpdateControl | midi.REC_SetChanged)
        if not self._check_and_show_hint() and SCRIPT_VERSION >= 8:
            param_name = plugins.getParamName(param_id, plugin_idx)
            param_value = plugins.getParamValue(param_id, plugin_idx) / 1016.0 * 100.0
            self._display_hint(param_name, '%0.2f' % param_value)

    def _set_mixer_param(self, param_id, value, incremental=False, track_index=0, plugin_index=0):
        event_id = mixer.getTrackPluginId(track_index, plugin_index) + param_id
        if incremental:
            value = channels.incEventValue(event_id, value, 0.01)
        else:
            value = ArturiaInputControls._to_rec_value(value, limit=12800)

        general.processRECEvent(
            event_id, value, midi.REC_UpdateValue | midi.REC_UpdatePlugLabel | midi.REC_ShowHint
                             | midi.REC_UpdateControl | midi.REC_SetChanged)
        if incremental:
            self._check_and_show_hint()

    def _set_mixer_param_fn(self, param_id, incremental=False, track_index=0, plugin_index=0):
        return lambda v: self._set_mixer_param(
            param_id, v, incremental=incremental, track_index=track_index, plugin_index=plugin_index)

    def _set_plugin_param_fn(self, param_id, incremental=False):
        return lambda v: self._set_plugin_param(param_id, v, incremental=incremental)

    def _plugin_map_for(self, offsets, incremental=False):
        return [self._set_plugin_param_fn(x, incremental=incremental) for x in offsets]

    def _mixer_map_for(self, param_id, track_indices, incremental=False):
        return [self._set_mixer_param_fn(param_id, track_index=t, incremental=incremental)
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
            '': [
                self._mixer_map_for(midi.REC_Mixer_Vol, [1, 2, 3, 4, 5, 6, 7, 8, 0]),
                self._mixer_map_for(midi.REC_Mixer_Vol, [9, 10, 11, 12, 13, 14, 15, 16, 0]),
                self._mixer_map_for(midi.REC_Mixer_Vol, [17, 18, 19, 20, 21, 22, 23, 24, 0]),
                self._mixer_map_for(midi.REC_Mixer_Vol, [25, 26, 27, 28, 29, 30, 31, 32, 0]),
                self._mixer_map_for(midi.REC_Mixer_Vol, [33, 34, 35, 36, 37, 38, 39, 40, 0]),
                # If you need more tracks for mixer sliders, add below here...
            ],
        }

        self._knobs_map[ArturiaInputControls.INPUT_MODE_MIXER_OVERVIEW] = {
            '': [
                self._mixer_map_for(midi.REC_Mixer_Pan, [1, 2, 3, 4, 5, 6, 7, 8, 0], incremental=True),
                self._mixer_map_for(midi.REC_Mixer_SS, [1, 2, 3, 4, 5, 6, 7, 8, 0], incremental=True),

                self._mixer_map_for(midi.REC_Mixer_Pan, [9, 10, 11, 12, 13, 14, 15, 16, 0], incremental=True),
                self._mixer_map_for(midi.REC_Mixer_SS, [9, 10, 11, 12, 13, 14, 15, 16, 0], incremental=True),

                self._mixer_map_for(midi.REC_Mixer_Pan, [17, 18, 19, 20, 21, 22, 23, 24, 0], incremental=True),
                self._mixer_map_for(midi.REC_Mixer_SS, [17, 18, 19, 20, 21, 22, 23, 24, 0], incremental=True),

                self._mixer_map_for(midi.REC_Mixer_Pan, [25, 26, 27, 28, 29, 30, 31, 32, 0], incremental=True),
                self._mixer_map_for(midi.REC_Mixer_SS, [25, 26, 27, 28, 29, 30, 31, 32, 0], incremental=True),

                self._mixer_map_for(midi.REC_Mixer_Pan, [33, 34, 35, 36, 37, 38, 39, 40, 0], incremental=True),
                self._mixer_map_for(midi.REC_Mixer_SS, [33, 34, 35, 36, 37, 38, 39, 40, 0], incremental=True),

                # If you need more tracks for mixer knobs, add below here...
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
            knob_mapping = _auto_generate_knobs_mapping(channels.selectedChannel())
            if knob_mapping:
                self._knobs_map[self._current_mode][knob_mode] = [self._plugin_map_for(knob_mapping, incremental=True)]
            else:
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
            knob_mapping = _auto_generate_knobs_mapping(channels.selectedChannel())
            if knob_mapping:
                self._knobs_map[self._current_mode][knob_key] = [self._plugin_map_for(knob_mapping, incremental=True)]
                return [_auto_generate_knobs_mapping(channels.selectedChannel())]
            else:
                self._last_unknown_knob_mode = knob_key
                log('WARNING', 'No encoder mapping for plugin <%s>' % knob_key)
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
            self._display_unset()
            return

        # Assume index is always valid
        knobs = pages[self._knobs_mode_index]

        # Check if knob is mapped
        if knob_index >= len(knobs):
            # Knob is unmapped in the array
            self._display_unset()
            return

        knobs[knob_index](delta)
        return self

    def ProcessSliderInput(self, slider_index, value):
        pages = self._get_slider_pages()
        if len(pages) == 0:
            # Slider mode is invalid
            self._display_unset()
            return

        # Assume index is always valid
        sliders = pages[self._sliders_mode_index]

        # Check if knob is mapped
        if slider_index >= len(sliders):
            # Slider is unmapped in the array
            self._display_unset()
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

    def _display_unset(self):
        self._display_hint(' (UNSET) ', ' ')

    def _check_and_show_hint(self):
        hint = ui.getHintMsg()
        if not hint:
            return False

        lines = hint.split(':', 1)
        if len(lines) == 1:
            lines.append(' ')
        self._display_hint(lines[0], lines[1][:16])
        return True

    def _get_pad_position(self, index):
        return int(index / 4) % 2, index % 4

    def _update_lights(self):
        # Set 4x4 Pad lights to indicate the current configuration
        is_channel_mode = self._current_mode == ArturiaInputControls.INPUT_MODE_CHANNEL_PLUGINS
        is_mixer_mode = self._current_mode == ArturiaInputControls.INPUT_MODE_MIXER_OVERVIEW

        self._lights.SetLights({
            ArturiaLights.ID_BANK_NEXT: ArturiaLights.AsOnOffByte(is_channel_mode),
            ArturiaLights.ID_BANK_PREVIOUS: ArturiaLights.AsOnOffByte(is_mixer_mode),
        })
