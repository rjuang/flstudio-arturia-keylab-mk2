from macro_actions import Actions
from macro_actions import ENCODER1, ENCODER2, ENCODER3, ENCODER4, ENCODER5, ENCODER6, ENCODER7, ENCODER8, ENCODER9
from macro_actions import LOOP_BUTTON, LEFT_BUTTON, REC_BUTTON, RIGHT_BUTTON, PLAY_BUTTON, SAVE_BUTTON, STOP_BUTTON
from macro_actions import NAV_WHEEL

import _thread
import config_macros
import ui

DEFAULT_MACRO_MAP = {
    # The bindings specified here will be:
    #  (modifier_key, select button) :  action_key

    # Transport loop + Bank button
    (LOOP_BUTTON, 0): Actions.undo,
    (LOOP_BUTTON, 1): Actions.redo,
    (LOOP_BUTTON, 2): Actions.toggle_playlist_visibility,
    (LOOP_BUTTON, 3): Actions.toggle_channel_rack_visibility,
    (LOOP_BUTTON, 4): Actions.toggle_piano_roll_visibility,
    (LOOP_BUTTON, 5): Actions.toggle_mixer_visibility,
    (LOOP_BUTTON, 6): Actions.toggle_browser_visibility,
    (LOOP_BUTTON, 7): Actions.toggle_plugin_visibility,
    (LOOP_BUTTON, NAV_WHEEL): Actions.horizontal_zoom,
    (LOOP_BUTTON, ENCODER1): Actions.scale_input_by(1, Actions.strip_jog),
    (LOOP_BUTTON, ENCODER2): Actions.scale_input_by(2, Actions.strip_jog),
    (LOOP_BUTTON, ENCODER3): Actions.scale_input_by(4, Actions.strip_jog),
    (LOOP_BUTTON, ENCODER4): Actions.scrub_move_vertical,
    (LOOP_BUTTON, ENCODER5): Actions.noop,
    (LOOP_BUTTON, ENCODER6): Actions.noop,
    (LOOP_BUTTON, ENCODER7): Actions.noop,
    (LOOP_BUTTON, ENCODER8): Actions.noop,
    (LOOP_BUTTON, ENCODER9): Actions.noop,

    # Record + Bank button
    (REC_BUTTON, 0): Actions.close_all_plugin_windows,
    (REC_BUTTON, 1): Actions.cycle_active_window,
    (REC_BUTTON, 2): Actions.name_next_empty_pattern,
    (REC_BUTTON, 3): Actions.rename_and_color,
    (REC_BUTTON, 4): Actions.clone_pattern,
    (REC_BUTTON, 5): Actions.enter,
    (REC_BUTTON, 6): Actions.escape,
    (REC_BUTTON, 7): Actions.shortcut('delete', display='Delete selected'),
    (REC_BUTTON, NAV_WHEEL): Actions.scrub_time_by_quarter_bars,
    (REC_BUTTON, ENCODER1): Actions.scrub_time_by_ticks,
    (REC_BUTTON, ENCODER2): Actions.scrub_time_by_sixteenth_steps,
    (REC_BUTTON, ENCODER3): Actions.scrub_time_by_eigth_steps,
    (REC_BUTTON, ENCODER4): Actions.scrub_time_by_quarter_steps,
    (REC_BUTTON, ENCODER5): Actions.scrub_time_by_half_steps,
    (REC_BUTTON, ENCODER6): Actions.scrub_time_by_eigth_bars,
    (REC_BUTTON, ENCODER7): Actions.scrub_time_by_quarter_bars,
    (REC_BUTTON, ENCODER8): Actions.scrub_time_by_half_bars,
    (REC_BUTTON, ENCODER9): Actions.scrub_time_by_bars,

    # Play + Bank button
    (PLAY_BUTTON, 0): Actions.rewind_to_beginning,
    (PLAY_BUTTON, 1): Actions.mute_current_playlist_track,
    (PLAY_BUTTON, 2): Actions.playlist_track_prev,
    (PLAY_BUTTON, 3): Actions.playlist_track_next,
    (PLAY_BUTTON, 4): Actions.duplicate,
    (PLAY_BUTTON, 5): Actions.pianoroll_quick_legato,
    (PLAY_BUTTON, 6): Actions.pianoroll_quick_quantize,
    (PLAY_BUTTON, 7): Actions.pianoroll_quick_quantize_start_times,
    (PLAY_BUTTON, NAV_WHEEL): Actions.vertical_zoom,
    (PLAY_BUTTON, ENCODER1): Actions.noop,
    (PLAY_BUTTON, ENCODER2): Actions.noop,
    (PLAY_BUTTON, ENCODER3): Actions.noop,
    (PLAY_BUTTON, ENCODER4): Actions.noop,
    (PLAY_BUTTON, ENCODER5): Actions.noop,
    (PLAY_BUTTON, ENCODER6): Actions.noop,
    (PLAY_BUTTON, ENCODER7): Actions.noop,
    (PLAY_BUTTON, ENCODER8): Actions.noop,
    (PLAY_BUTTON, ENCODER9): Actions.noop,

    # Stop + Bank button
    (STOP_BUTTON, 0): Actions.deselect_all,
    (STOP_BUTTON, 1): Actions.add_time_marker,
    (STOP_BUTTON, 2): Actions.step_back_one_bar,
    (STOP_BUTTON, 3): Actions.step_one_bar,
    (STOP_BUTTON, 4): Actions.jump_prev_time_marker,
    (STOP_BUTTON, 5): Actions.jump_next_time_marker,
    (STOP_BUTTON, 6): Actions.select_prev_time_marker,
    (STOP_BUTTON, 7): Actions.select_next_time_marker,
    (STOP_BUTTON, NAV_WHEEL): Actions.jog2,
    (STOP_BUTTON, ENCODER1): Actions.repeated(Actions.scrub_move_horizontal),
    (STOP_BUTTON, ENCODER2): Actions.repeated(Actions.scrub_move_vertical),
    (STOP_BUTTON, ENCODER3): Actions.noop,
    (STOP_BUTTON, ENCODER4): Actions.noop,
    (STOP_BUTTON, ENCODER5): Actions.noop,
    (STOP_BUTTON, ENCODER6): Actions.noop,
    (STOP_BUTTON, ENCODER7): Actions.noop,
    (STOP_BUTTON, ENCODER8): Actions.noop,
    (STOP_BUTTON, ENCODER9): Actions.noop,

    # Nav Right arrow + Bank button
    (RIGHT_BUTTON, 0): Actions.open_mixer_plugin,
    (RIGHT_BUTTON, 1): Actions.open_mixer_plugin,
    (RIGHT_BUTTON, 2): Actions.open_mixer_plugin,
    (RIGHT_BUTTON, 3): Actions.open_mixer_plugin,
    (RIGHT_BUTTON, 4): Actions.open_mixer_plugin,
    (RIGHT_BUTTON, 5): Actions.open_mixer_plugin,
    (RIGHT_BUTTON, 6): Actions.open_mixer_plugin,
    (RIGHT_BUTTON, 7): Actions.open_mixer_plugin,
    (RIGHT_BUTTON, NAV_WHEEL): Actions.mixer_window_jog,
    (RIGHT_BUTTON, ENCODER1): Actions.scrub_selection_end_by_sixteenth_steps,
    (RIGHT_BUTTON, ENCODER2): Actions.scrub_selection_end_by_eighth_steps,
    (RIGHT_BUTTON, ENCODER3): Actions.scrub_selection_end_by_half_steps,
    (RIGHT_BUTTON, ENCODER4): Actions.scrub_selection_end_by_quarter_steps,
    (RIGHT_BUTTON, ENCODER5): Actions.scrub_selection_end_by_steps,
    (RIGHT_BUTTON, ENCODER6): Actions.scrub_selection_end_by_eighth_bars,
    (RIGHT_BUTTON, ENCODER7): Actions.scrub_selection_end_by_half_bars,
    (RIGHT_BUTTON, ENCODER8): Actions.scrub_selection_end_by_quarter_bars,
    (RIGHT_BUTTON, ENCODER9): Actions.scrub_selection_end_by_eighth_bars,

    # Nav Left arrow + Bank button
    (LEFT_BUTTON, 0): Actions.channel_rack_up,
    (LEFT_BUTTON, 1): Actions.channel_rack_down,
    (LEFT_BUTTON, 2): Actions.current_channel_toggle_mute,
    (LEFT_BUTTON, 3): Actions.clone_channel,
    (LEFT_BUTTON, 4): Actions.shortcut('Shift+C', display='Select source'),
    (LEFT_BUTTON, 5): Actions.cut,
    (LEFT_BUTTON, 6): Actions.copy,
    (LEFT_BUTTON, 7): Actions.paste,
    (LEFT_BUTTON, NAV_WHEEL): Actions.window_jog,
    (LEFT_BUTTON, ENCODER1): Actions.scrub_selection_start_by_sixteenth_steps,
    (LEFT_BUTTON, ENCODER2): Actions.scrub_selection_start_by_eighth_steps,
    (LEFT_BUTTON, ENCODER3): Actions.scrub_selection_start_by_half_steps,
    (LEFT_BUTTON, ENCODER4): Actions.scrub_selection_start_by_quarter_steps,
    (LEFT_BUTTON, ENCODER5): Actions.scrub_selection_start_by_steps,
    (LEFT_BUTTON, ENCODER6): Actions.scrub_selection_start_by_eighth_bars,
    (LEFT_BUTTON, ENCODER7): Actions.scrub_selection_start_by_quarter_bars,
    (LEFT_BUTTON, ENCODER8): Actions.scrub_selection_start_by_half_bars,
    (LEFT_BUTTON, ENCODER9): Actions.scrub_selection_start_by_bars,
}


class ArturiaMacroBank:
    def __init__(self, display_fn=None):
        if display_fn is None:
            def noop_display(line1, line2):
                pass
            display_fn = noop_display

        self._display_fn = display_fn
        self._macro_map = dict(DEFAULT_MACRO_MAP)
        self._lock = _thread.allocate_lock()
        for k, v in config_macros.OVERRIDE_MACROS.items():
            self._macro_map[k] = v

    def _count_bits_set(self, mask):
        cnt = 0
        while mask != 0:
            cnt += (mask & 1)
            mask >>= 1
        return cnt

    def _is_help_request(self, modifier_mask):
        return SAVE_BUTTON & modifier_mask

    def on_macro_actions(self, modifier_mask, macro_id, param_value):
        """Called when a macro action is requested.

        Args:
            modifier_mask: bit-mask containing information on what modifier buttons have been pressed.
            macro_id: integer specifying the value to look up the macro action (usually the channel bank index of the
              button pressed, or code specifying the encoder it came from)
            param_value: integer providing any additional information to the function (e.g. can be value of the
              channel the button corresponds to, or a delta value corresponding to the amount the knob turned)
        """
        self._lock.acquire()
        try:
            help_request = self._is_help_request(modifier_mask)
            modifier_mask &= ~SAVE_BUTTON
            key = (modifier_mask, macro_id)
            action = 'Help' if help_request else 'Macro'
            if key in self._macro_map:
                doc_str = self._macro_map[key].__doc__
                if doc_str:
                    self._display_fn(action, doc_str)
                    ui.setHintMsg('[%s] %s' % (action, doc_str))
                if not help_request:
                    self._macro_map[key](param_value)
        finally:
            self._lock.release()
