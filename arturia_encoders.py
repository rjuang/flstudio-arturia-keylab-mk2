import channels
import device
import general
import midi
import mixer
import transport
import ui

import arturia_leds
import arturia_midi
import config
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
        key = (channels.selectedChannel(), status, control_num)
        if key in self._plugin_knob_map:
            value = self._plugin_knob_map[key]
        value = min(127, max(0, value + delta))
        self._plugin_knob_map[key] = value
        return value

    def _get_current_toggle_values(self):
        key = (channels.selectedChannel(), self._current_index_plugin)
        if key in self._plugin_toggle_map:
            return self._plugin_toggle_map[key]
        return [False] * 9

    def _update_toggle_value(self, plugin_index, button_index):
        bank_values = [False] * 9
        key = (channels.selectedChannel(), plugin_index)
        if key in self._plugin_toggle_map:
            bank_values = self._plugin_toggle_map[key]
        bank_values[button_index] = not bank_values[button_index]
        self._plugin_toggle_map[key] = bank_values
        return 127 if bank_values[button_index] else 0

    def __init__(self, paged_display, lights):
        self._paged_display = paged_display
        self._lights = lights
        self._mixer_knobs_panning = True
        self._current_mode = ArturiaInputControls.INPUT_MODE_MIXER_OVERVIEW

        if config.SLIDERS_FIRST_CONTROL_PLUGINS:
            # Set the initial mode to plugins if requested.
            self._current_mode = ArturiaInputControls.INPUT_MODE_CHANNEL_PLUGINS

        self._plugin_knob_map = {}
        self._plugin_toggle_map = {}
        # Arturia keyboards only have 9 sliders
        self._mixer_slider_initial_values = [-1]*9

        self._last_hint_time_ms = 0

        self._current_index_mixer = 0
        self._current_index_plugin = 0

    def ToggleCurrentMode(self):
        self._current_mode = (self._current_mode + 1) % len(ArturiaInputControls.MODE_NAMES)
        self._display_hint('Controlling', ArturiaInputControls.MODE_NAMES[self._current_mode],
                           fl_hint=config.ENABLE_CONTROLS_FL_HINTS)
        self._update_lights()
        self._reset_sliders_pickup_status()

    def ToggleKnobMode(self):
        if self._current_mode == ArturiaInputControls.INPUT_MODE_MIXER_OVERVIEW:
            self._mixer_knobs_panning = not self._mixer_knobs_panning
            mode = 'Panning' if self._mixer_knobs_panning else 'Stereo Sep.'
            self._display_hint('Knobs Control', mode, fl_hint=config.ENABLE_CONTROLS_FL_HINTS)
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
        self._update_lights()
        self._reset_sliders_pickup_status()

    def PrevControlsPage(self):
        if self._current_mode == ArturiaInputControls.INPUT_MODE_MIXER_OVERVIEW:
            self._current_index_mixer = (self._current_index_mixer - 1) % ArturiaInputControls.MAX_NUM_PAGES
            self._display_mixer_update_hint()
        else:
            self._current_index_plugin = (self._current_index_plugin - 1) % ArturiaInputControls.MAX_NUM_PAGES
            self._display_plugin_update_hint()
        self._update_lights()
        self._reset_sliders_pickup_status()

    def _display_mixer_update_hint(self):
        begin_track = self._current_index_mixer * 8 + 1
        end_track = (self._current_index_mixer + 1) * 8
        self._display_hint('Controlling',
                           'Tracks %d - %d' % (begin_track, end_track),
                           fl_hint=config.ENABLE_CONTROLS_FL_HINTS)

    def _display_plugin_update_hint(self):
        self._display_hint('Setting MIDI Ch', 'To: %2d' % (self._current_index_plugin + 1),
                           fl_hint=config.ENABLE_CONTROLS_FL_HINTS)

    def ProcessKnobInput(self, knob_index, delta):
        if self._current_mode == ArturiaInputControls.INPUT_MODE_MIXER_OVERVIEW:
            self._process_knobs_mixer_track(knob_index, delta)
        else:
            self._process_plugin_knob_event(knob_index, delta)
        return self

    def _is_slider_picked_up(self, track_index, value):
        if not config.ENABLE_MIXER_SLIDERS_PICKUP_MODE:
            return True
        slider_index = 8
        if track_index > 0:
            slider_index = (track_index - 1) % 8
        initial_value = self._mixer_slider_initial_values[slider_index]
        if initial_value < 0:
            self._mixer_slider_initial_values[slider_index] = value
            return value == int(127.0 * mixer.getTrackVolume(track_index))

        daw_value = int(127.0 * mixer.getTrackVolume(track_index))
        if (initial_value <= daw_value <= value) or (value <= daw_value <= initial_value):
            self._mixer_slider_initial_values[slider_index] = 256
        return self._mixer_slider_initial_values[slider_index] > 255

    def _reset_sliders_pickup_status(self):
        self._mixer_slider_initial_values = [-1]*9

    def _process_sliders_track_volume(self, slider_index, value):
        track_index = (self._current_index_mixer * 8 + slider_index) + 1
        track_name = 'Track  %d' % track_index
        if slider_index == 8:
            track_index = 0
            track_name = 'Master Track'

        if self._is_slider_picked_up(track_index, value):
            self._set_mixer_param(midi.REC_Mixer_Vol, value, track_index=track_index)
            volume = int((value / 127.0) * 100.0)
            self._display_hint(track_name, 'Volume: %d%%' % volume)
        else:
            volume = int(mixer.getTrackVolume(track_index) * 100.0)
            self._display_hint(track_name, 'Volume: %d%% LOCK' % volume)

    def _process_plugin_slider_event(self, index, value):
        status = 176 + self._current_index_plugin
        data1 = 35 + index
        data2 = value
        message = status + (data1 << 8) + (data2 << 16) + (arturia_midi.PLUGIN_PORT_NUM << 24)
        device.forwardMIDICC(message, 2)
        pretty_value = int((value / 127) * 100)
        self._display_hint('Slider %d Ch: %2d' % (index + 1, self._current_index_plugin + 1),
                           '%3d%%  [%02X %02X %02X]' % (pretty_value, status, data1, data2),
                           fl_hint=config.ENABLE_CONTROLS_FL_HINTS)

    def _process_plugin_knob_event(self, index, delta):
        status = 176 + self._current_index_plugin
        data1 = 67 + index
        data2 = self._update_knob_value(status, data1, delta)
        message = status + (data1 << 8) + (data2 << 16) + (arturia_midi.PLUGIN_PORT_NUM << 24)
        device.forwardMIDICC(message, 2)
        pretty_value = int((data2 / 127) * 100)
        self._display_hint('Enc. %d  Ch: %2d' % (index + 1, self._current_index_plugin + 1),
                           '%3d%%  [%02X %02X %02X]' % (pretty_value, status, data1, data2),
                           fl_hint=config.ENABLE_CONTROLS_FL_HINTS)

    def _process_knobs_mixer_track(self, knob_index, delta):
        track_index = (self._current_index_mixer * 8 + knob_index) + 1
        if knob_index == 8:
            track_index = 0
        param_id = midi.REC_Mixer_Pan if self._mixer_knobs_panning else midi.REC_Mixer_SS
        self._set_mixer_param(param_id, delta, track_index=track_index, incremental=True)

    def _process_plugin_button_event(self, index):
        status = 176 + self._current_index_plugin
        data1 = 22 + index
        data2 = self._update_toggle_value(self._current_index_plugin, index)
        message = status + (data1 << 8) + (data2 << 16) + (arturia_midi.PLUGIN_PORT_NUM << 24)
        device.forwardMIDICC(message, 2)
        self._display_hint('Plugin button',
                           '%02X %02X %02X' % (status, data1, data2),
                           fl_hint=config.ENABLE_CONTROLS_FL_HINTS)
        self._update_lights()

    def ProcessSliderInput(self, slider_index, value):
        if self._current_mode == ArturiaInputControls.INPUT_MODE_MIXER_OVERVIEW:
            self._process_sliders_track_volume(slider_index, value)
        else:
            self._process_plugin_slider_event(slider_index, value)
        return self

    def ProcessBankSelection(self, button_index):
        if self._current_mode != ArturiaInputControls.INPUT_MODE_CHANNEL_PLUGINS:
            self._select_one_channel(button_index + (8 * self._current_index_mixer))
        else:
            self._process_plugin_button_event(button_index)

    def StartOrEndSliderInput(self):
        pass

    def Refresh(self):
        self._update_lights()

    def _display_hint(self, hint_title, hint_value, fl_hint=False):
        if config.HINT_DISPLAY_ALL_CAPS:
            hint_title = hint_title.upper()
            hint_value = hint_value.upper()

        hint_title = ArturiaDisplay.abbreviate(hint_title)

        self._paged_display.SetPageLines('hint', line1=hint_title, line2=hint_value)
        current_time_ms = ArturiaDisplay.time_ms()

        if fl_hint:
            ui.setHintMsg('%s %s' % (hint_title, hint_value))

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
        is_plugin_mode = self._current_mode == ArturiaInputControls.INPUT_MODE_CHANNEL_PLUGINS

        self._lights.SetLights({
            ArturiaLights.ID_BANK_NEXT: ArturiaLights.AsOnOffByte(is_knobs_panning),
            ArturiaLights.ID_BANK_PREVIOUS: ArturiaLights.AsOnOffByte(is_mixer_mode),
        })

        channel_idx = channels.selectedChannel()
        selected_idx = channel_idx - (self._current_index_mixer * 8)

        if is_plugin_mode:
            values = [ArturiaLights.rgb2int(0x7F, 0, 0) if v else 0 for v in self._get_current_toggle_values()]
            self._lights.SetBankLights(values, rgb=True)
        else:
            values = [0]*9
            if config.ENABLE_COLORIZE_BANK_LIGHTS:
                for i in range(8):
                    idx = (self._current_index_mixer * 8) + i
                    if idx < channels.channelCount():
                        values[i] = ArturiaLights.fadedColor(channels.getChannelColor(idx))

            # Bank lights
            if not arturia_leds.ESSENTIAL_KEYBOARD:
                if config.ENABLE_COLORIZE_BANK_LIGHTS:
                    if 0 <= selected_idx < 8:
                        values[selected_idx] = ArturiaLights.fullColor(channels.getChannelColor(channel_idx))
                    self._lights.SetBankLights(values, rgb=True)
                else:
                    if 0 <= selected_idx < 8:
                        values[selected_idx] = ArturiaLights.LED_ON
                    self._lights.SetBankLights(values, rgb=False)

        # Pad lights
        should_color_pads = ((arturia_leds.ESSENTIAL_KEYBOARD and config.ENABLE_COLORIZE_BANK_LIGHTS) or
                             (not arturia_leds.ESSENTIAL_KEYBOARD and config.ENABLE_MK2_COLORIZE_PAD_LIGHTS))

        if should_color_pads:
            selected_color = ArturiaLights.fadedColor(channels.getChannelColor(channel_idx))
            pad_values = ArturiaLights.ZeroMatrix(zero=selected_color)
            self._lights.SetPadLights(pad_values, rgb=True)

    def _select_one_channel(self, index):
        if index >= channels.channelCount() or index < 0:
            return
        if SCRIPT_VERSION >= 8:
            channels.selectOneChannel(index)
        else:
            channels.deselectAll()
            channels.selectChannel(index, 1)

