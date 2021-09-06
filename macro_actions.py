""" Defines all constants and available actions that can be linked to a macro button. """
import channels
import general
import midi
import transport
import ui


SCRIPT_VERSION = general.getVersion()

# These represent the bit in which the button must be held.
# For a macro that requires two modifiers to be held, simply add the constants.

# Bitmask for loop button
LOOP_BUTTON = 1
# Bitmask for record button
REC_BUTTON = 2
# Bitmask for play button
PLAY_BUTTON = 4
# Bitmask for stop button
STOP_BUTTON = 8
# Bitmask for left nav arrow
LEFT_BUTTON = 16
# Bitmask for right nav arrow
RIGHT_BUTTON = 32
# Bitmask for save button (song/pattern button)
SAVE_BUTTON = 64


class Actions:
    """Class that houses all action functions available.

    TODO: Doc-strings might be able to be used to document the macro. This could be used to allow for a two-button press
    plus bank button to display the doc-string to the user. As such, try to limit doc strings to 16-chars for future
    help-system implementation.
    """
    @staticmethod
    def toggle_playlist_visibility():
        """Playlist"""
        transport.globalTransport(midi.FPT_F5, 1)

    @staticmethod
    def toggle_channel_rack_visibility():
        """Channel Rack"""
        transport.globalTransport(midi.FPT_F6, 1)

    @staticmethod
    def toggle_piano_roll_visibility():
        """Piano Roll"""
        transport.globalTransport(midi.FPT_F7, 1)

    @staticmethod
    def toggle_mixer_visibility():
        """Toggle mixer"""
        transport.globalTransport(midi.FPT_F9, 1)

    @staticmethod
    def toggle_browser_visibility():
        """Toggle browser"""
        if ui.getVisible(midi.widBrowser):
            ui.hideWindow(midi.widBrowser)
        else:
            ui.showWindow(midi.widBrowser)
            ui.setFocused(midi.widBrowser)

    @staticmethod
    def toggle_plugin_visibility():
        """Toggle plugin"""
        if SCRIPT_VERSION >= 9:
            channels.showCSForm(channels.channelNumber(), -1)
        else:
            channels.focusEditor(channels.channelNumber())

    @staticmethod
    def undo():
        """Undo"""
        general.undoUp()

    @staticmethod
    def redo():
        """Redo"""
        general.undoDown()

    @staticmethod
    def noop():
        """Not assigned"""
        # Do nothing
        pass
