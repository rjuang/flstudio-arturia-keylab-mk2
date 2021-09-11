from macro_actions import Actions
from macro_actions import LOOP_BUTTON, LEFT_BUTTON, REC_BUTTON, RIGHT_BUTTON, PLAY_BUTTON, SAVE_BUTTON, STOP_BUTTON

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

    # Record + Bank button
    (REC_BUTTON, 0): Actions.close_all_plugin_windows,
    (REC_BUTTON, 1): Actions.cycle_active_window,
    (REC_BUTTON, 2): Actions.name_next_empty_pattern,
    (REC_BUTTON, 3): Actions.rename_and_color,
    (REC_BUTTON, 4): Actions.clone_pattern,
    (REC_BUTTON, 5): Actions.noop,
    (REC_BUTTON, 6): Actions.enter,
    (REC_BUTTON, 7): Actions.escape,

    # Play + Bank button
    (PLAY_BUTTON, 0): Actions.channel_rack_up,
    (PLAY_BUTTON, 1): Actions.channel_rack_down,
    (PLAY_BUTTON, 2): Actions.noop,
    (PLAY_BUTTON, 3): Actions.noop,
    (PLAY_BUTTON, 4): Actions.noop,
    (PLAY_BUTTON, 5): Actions.pianoroll_quick_legato,
    (PLAY_BUTTON, 6): Actions.pianoroll_quick_quantize,
    (PLAY_BUTTON, 7): Actions.pianoroll_quick_quantize_start_times,

    # Stop + Bank button
    (STOP_BUTTON, 0): Actions.rewind_to_beginning,
    (STOP_BUTTON, 1): Actions.noop,
    (STOP_BUTTON, 2): Actions.noop,
    (STOP_BUTTON, 3): Actions.noop,
    (STOP_BUTTON, 4): Actions.noop,
    (STOP_BUTTON, 5): Actions.noop,
    (STOP_BUTTON, 6): Actions.noop,
    (STOP_BUTTON, 7): Actions.noop,

    # Nav Right arrow + Bank button
    (RIGHT_BUTTON, 0): Actions.open_mixer_plugin,
    (RIGHT_BUTTON, 1): Actions.open_mixer_plugin,
    (RIGHT_BUTTON, 2): Actions.open_mixer_plugin,
    (RIGHT_BUTTON, 3): Actions.open_mixer_plugin,
    (RIGHT_BUTTON, 4): Actions.open_mixer_plugin,
    (RIGHT_BUTTON, 5): Actions.open_mixer_plugin,
    (RIGHT_BUTTON, 6): Actions.open_mixer_plugin,
    (RIGHT_BUTTON, 7): Actions.open_mixer_plugin,

    # Nav Left arrow + Bank button
    (LEFT_BUTTON, 0): Actions.duplicate,
    (LEFT_BUTTON, 1): Actions.noop,
    (LEFT_BUTTON, 2): Actions.noop,
    (LEFT_BUTTON, 3): Actions.noop,
    (LEFT_BUTTON, 4): Actions.noop,
    (LEFT_BUTTON, 5): Actions.noop,
    (LEFT_BUTTON, 6): Actions.noop,
    (LEFT_BUTTON, 7): Actions.noop,

    # Save + Bank button
    (SAVE_BUTTON, 0): Actions.noop,
    (SAVE_BUTTON, 1): Actions.noop,
    (SAVE_BUTTON, 2): Actions.noop,
    (SAVE_BUTTON, 3): Actions.noop,
    (SAVE_BUTTON, 4): Actions.noop,
    (SAVE_BUTTON, 5): Actions.noop,
    (SAVE_BUTTON, 6): Actions.noop,
    (SAVE_BUTTON, 7): Actions.noop,
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

    def on_channel_bank(self, modifier_mask, bank_index, channel_index):
        self._lock.acquire()
        try:
            help_request = self._is_help_request(modifier_mask)
            modifier_mask &= ~SAVE_BUTTON
            key = (modifier_mask, bank_index)
            action = 'Help' if help_request else 'Macro'
            if key in self._macro_map:
                doc_str = self._macro_map[key].__doc__
                if doc_str:
                    self._display_fn(action, doc_str)
                    ui.setHintMsg('[%s] %s' % (action, doc_str))
                if not help_request:
                    self._macro_map[key](channel_index)
        finally:
            self._lock.release()
