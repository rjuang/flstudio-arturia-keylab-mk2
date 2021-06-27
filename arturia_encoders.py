import channels
import device
import general
import midi
import mixer
import transport
import ui

import arturia_midi
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
    MAX_NUM_PAGES = 16   # Bank 0-F for plugins and 0 - 127 for mixer

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

    def _update_knob_value(self, status, control_num, delta):
        value = 64
        key = (status, control_num)
        if key in self._plugin_knob_map:
            value = self._plugin_knob_map[key]
        value = min(127, max(0, value + delta))
        self._plugin_knob_map[key] = value
        return value

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
        self._mixer_knobs_panning = True
        self._current_mode = ArturiaInputControls.INPUT_MODE_MIXER_OVERVIEW
        self._plugin_knob_map = {}

        # Maps a string containing the input control mode to another dictionary containing a mapping of
        # the plugin names to an array of lambda functions to execute for the corresponding offset.
        self._knobs_map = {}
        self._sliders_map = {}

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

        self._current_index_mixer = 0
        self._current_index_plugin = 0

    def ToggleCurrentMode(self):
        self._current_mode = (self._current_mode + 1) % len(ArturiaInputControls.MODE_NAMES)
        self._display_hint('Controlling', ArturiaInputControls.MODE_NAMES[self._current_mode])
        self._update_lights()

    def ToggleKnobMode(self):
        if self._current_mode == ArturiaInputControls.INPUT_MODE_MIXER_OVERVIEW:
            self._mixer_knobs_panning = not self._mixer_knobs_panning
            mode = 'Panning' if self._mixer_knobs_panning else 'Stereo Sep.'
            self._display_hint('Knobs Control', mode)
            self._update_lights()
        else:
            # TODO: Toggle knob mode for Plugin mode.
            # Maybe increment channel ?
            self._display_hint('Not implemented', 'TODO')

    def NextControlsPage(self):
        if self._current_mode == ArturiaInputControls.INPUT_MODE_MIXER_OVERVIEW:
            self._current_index_mixer = (self._current_index_mixer + 1) % ArturiaInputControls.MAX_NUM_PAGES
            self._display_mixer_update_hint()
        else:
            self._current_index_plugin = (self._current_index_plugin + 1) % ArturiaInputControls.MAX_NUM_PAGES
            self._display_plugin_update_hint()

    def PrevControlsPage(self):
        if self._current_mode == ArturiaInputControls.INPUT_MODE_MIXER_OVERVIEW:
            self._current_index_mixer = (self._current_index_mixer - 1) % ArturiaInputControls.MAX_NUM_PAGES
            self._display_mixer_update_hint()
        else:
            self._current_index_plugin = (self._current_index_plugin - 1) % ArturiaInputControls.MAX_NUM_PAGES
            self._display_plugin_update_hint()

    def _display_mixer_update_hint(self):
        begin_track = self._current_index_mixer * 8 + 1
        end_track = (self._current_index_mixer + 1) * 8
        self._display_hint('Controlling', 'Tracks %d - %d' % (begin_track, end_track))

    def _display_plugin_update_hint(self):
        self._display_hint('Controls on Bank', '%d' % self._current_index_plugin)

    def ProcessKnobInput(self, knob_index, delta):
        if self._current_mode == ArturiaInputControls.INPUT_MODE_MIXER_OVERVIEW:
            self._process_knobs_mixer_track(knob_index, delta)
        else:
            self._process_plugin_knob_event(knob_index, delta)
        return self

    def _process_sliders_track_volume(self, slider_index, value):
        track_index = (self._current_index_mixer * 8 + slider_index) + 1
        track_name = 'Track %d' % track_index
        if slider_index == 8:
            track_index = 0
            track_name = 'Master Track'
        self._set_mixer_param(midi.REC_Mixer_Vol, value, track_index=track_index)
        volume = int((value / 127.0) * 100.0)
        self._display_hint(track_name, 'Volume %d%%' % volume)

    def _process_plugin_slider_event(self, index, value):
        status = 176 + self._current_index_plugin
        data1 = 35 + index
        data2 = value
        message = status + (data1 << 8) + (data2 << 16) + (arturia_midi.PLUGIN_PORT_NUM << 24)
        device.forwardMIDICC(message, 2)
        self._display_hint('Plugin fader', '%02X %02X %02X' % (status, data1, data2))

    def _process_plugin_knob_event(self, index, delta):
        status = 176 + self._current_index_plugin
        data1 = 67 + index
        data2 = self._update_knob_value(status, data1, delta)
        message = status + (data1 << 8) + (data2 << 16) + (arturia_midi.PLUGIN_PORT_NUM << 24)
        device.forwardMIDICC(message, 2)
        self._display_hint('Plugin encoder', '%02X %02X %02X' % (status, data1, data2))

    def _process_knobs_mixer_track(self, knob_index, delta):
        track_index = (self._current_index_mixer * 8 + knob_index) + 1
        if knob_index == 8:
            track_index = 0
        param_id = midi.REC_Mixer_Pan if self._mixer_knobs_panning else midi.REC_Mixer_SS
        self._set_mixer_param(param_id, delta, track_index=track_index, incremental=True)

    def ProcessSliderInput(self, slider_index, value):
        if self._current_mode == ArturiaInputControls.INPUT_MODE_MIXER_OVERVIEW:
            self._process_sliders_track_volume(slider_index, value)
        else:
            self._process_plugin_slider_event(slider_index, value)
        return self

    def StartOrEndSliderInput(self):
        pass

    def Refresh(self):
        # Don't update lights if recording
        if not transport.isRecording() and not transport.isPlaying():
            self._update_lights()

    def _display_hint(self, hint_title, hint_value):
        hint_title = ArturiaDisplay.abbreviate(hint_title)

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

    def _update_lights(self):
        is_knobs_panning = (self._current_mode == ArturiaInputControls.INPUT_MODE_MIXER_OVERVIEW and
                            self._mixer_knobs_panning)
        is_mixer_mode = self._current_mode == ArturiaInputControls.INPUT_MODE_MIXER_OVERVIEW

        self._lights.SetLights({
            ArturiaLights.ID_BANK_NEXT: ArturiaLights.AsOnOffByte(is_knobs_panning),
            ArturiaLights.ID_BANK_PREVIOUS: ArturiaLights.AsOnOffByte(is_mixer_mode),
        })
