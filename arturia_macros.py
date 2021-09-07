from macro_actions import Actions
from macro_actions import LOOP_BUTTON, LEFT_BUTTON, REC_BUTTON, RIGHT_BUTTON, PLAY_BUTTON, SAVE_BUTTON, STOP_BUTTON

import config_macros

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
    (REC_BUTTON, 2): Actions.name_first_empty_pattern,
    (REC_BUTTON, 3): Actions.name_next_empty_pattern,
    (REC_BUTTON, 4): Actions.rename_and_color,
    (REC_BUTTON, 5): Actions.clone_pattern,
    (REC_BUTTON, 6): Actions.noop,
    (REC_BUTTON, 7): Actions.toggle_script_output_visibility,

    # Play + Bank button
    (PLAY_BUTTON, 0): Actions.noop,
    (PLAY_BUTTON, 1): Actions.noop,
    (PLAY_BUTTON, 2): Actions.noop,
    (PLAY_BUTTON, 3): Actions.noop,
    (PLAY_BUTTON, 4): Actions.noop,
    (PLAY_BUTTON, 5): Actions.noop,
    (PLAY_BUTTON, 6): Actions.noop,
    (PLAY_BUTTON, 7): Actions.noop,

    # Stop + Bank button
    (STOP_BUTTON, 0): Actions.noop,
    (STOP_BUTTON, 1): Actions.noop,
    (STOP_BUTTON, 2): Actions.noop,
    (STOP_BUTTON, 3): Actions.noop,
    (STOP_BUTTON, 4): Actions.noop,
    (STOP_BUTTON, 5): Actions.noop,
    (STOP_BUTTON, 6): Actions.noop,
    (STOP_BUTTON, 7): Actions.noop,

    # Nav Right arrow + Bank button
    (RIGHT_BUTTON, 0): Actions.noop,
    (RIGHT_BUTTON, 1): Actions.noop,
    (RIGHT_BUTTON, 2): Actions.noop,
    (RIGHT_BUTTON, 3): Actions.noop,
    (RIGHT_BUTTON, 4): Actions.noop,
    (RIGHT_BUTTON, 5): Actions.noop,
    (RIGHT_BUTTON, 6): Actions.noop,
    (RIGHT_BUTTON, 7): Actions.noop,

    # Nav Left arrow + Bank button
    (LEFT_BUTTON, 0): Actions.noop,
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
    def __init__(self):
        self._macro_map = dict(DEFAULT_MACRO_MAP)
        for k, v in config_macros.OVERRIDE_MACROS.items():
            self._macro_map[k] = v

    def on_channel_bank(self, modifier_mask, bank_index):
        key = (modifier_mask, bank_index)
        if key in self._macro_map:
            self._macro_map[key]()