from macro_actions import Actions
from macro_actions import ENCODER1, ENCODER2, ENCODER3, ENCODER4, ENCODER5, ENCODER6, ENCODER7, ENCODER8, ENCODER9
from macro_actions import LOOP_BUTTON, LEFT_BUTTON, REC_BUTTON, RIGHT_BUTTON, PLAY_BUTTON, SAVE_BUTTON, STOP_BUTTON
from macro_actions import NAV_WHEEL

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
    #
    # (LOOP_BUTTON, NAV_WHEEL): Actions.horizontal_zoom,
    # (LOOP_BUTTON, ENCODER1): Actions.strip_jog,
    # (LOOP_BUTTON, ENCODER2): Actions.scale_input_by(2, Actions.strip_jog),
}
