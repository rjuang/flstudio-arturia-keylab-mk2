from macro_actions import Actions
from macro_actions import LOOP_BUTTON, LEFT_BUTTON, REC_BUTTON, RIGHT_BUTTON, PLAY_BUTTON, SAVE_BUTTON, STOP_BUTTON

OVERRIDE_MACROS = {
    # Override the default macro assignment with a custom action.
    # Examples:
    # (LOOP_BUTTON, 0): Actions.undo,      # Loop button + bank 0 maps to undo
    # (LEFT_BUTTON, 1): Actions.redo,      # Left nav button + bank 1 maps to redo
    # (RIGHT_BUTTON, 2): Actions.redo,
    # (REC_BUTTON, 3): Actions.redo,
    # (PLAY_BUTTON, 4): Actions.redo,
    # (SAVE_BUTTON, 5): Actions.redo,
    # (STOP_BUTTON, 6): Actions.redo,
}
