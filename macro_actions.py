""" Defines all constants and available actions that can be linked to a macro button. """
import channels
import general
import midi
import transport
import ui

import time

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

# Number of times the left arrow needs to be clicked to reach the menu item.
# NOTE: Do NOT use "right" arrow because that key can enter the menu.
_MENU_LEFT_COUNT = {
    'file': 0,
    'edit': 7,
    'add': 6,
    'patterns': 5,
    'view': 4,
    'options': 3,
    'tools': 2,
    'help': 1,
}

# Number of times the down arrow needs to be clicked to reach the menu item.
_MENU_DOWN_COUNT = {
    # View menu
    'playlist': 1,
    'piano roll': 2,
    'channel rack': 3,
    'mixer': 4,
    'browser': 5,
    'project picker': 6,
    'plugin picker': 7,
    'tempo tapper': 8,
    'touch controller': 9,
    'script output': 10,
    'toolbars': 11,
    'tests': 12,
    'plugin performance monitor': 13,
    'close all windows': 14,
    'close all plugin windows': 15,
    'close all unfocused windows': 16,
    'align all channel editors': 17,
    'arrange windows': 18,
    'background': 19,
    'undo history': 20,
    'patterns': 21,
    'generators in use': 22,
    'effects in use': 23,
    'remote control': 24,
    'plugin database': 25,
}


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
            if SCRIPT_VERSION <= 12:  # As of 20.8.4 and earlier, widBrowser doesn't properly show the browser window.
                # Hacky way to toggle browser window.
                # Public rant: FL Studio does not have a way to send modifier keys in their shortcut, nor any way to
                # access menu items via API. This is a hacky way to do this.
                Actions._open_app_menu()
                time.sleep(0.1)
                Actions._navigate_to_menu('view', 'browser')
                Actions._press_enter()
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

    @staticmethod
    def _press_enter():
        transport.globalTransport(midi.FPT_Enter, 1)

    @staticmethod
    def _open_app_menu():
        # FPT_Menu needs to be triggered when channel rack in focus in order to bring up the app menu.
        # Save the visibility state of the channel rack and restore at the end.
        channel_rack_visible = ui.getVisible(midi.widChannelRack)
        if not channel_rack_visible:
            ui.showWindow(midi.widChannelRack)
        ui.setFocused(midi.widChannelRack)
        transport.globalTransport(midi.FPT_Menu, 1)
        if not channel_rack_visible:
            ui.hideWindow(midi.widChannelRack)

    @staticmethod
    def _navigate_to_menu(menu, item):
        for _ in range(_MENU_LEFT_COUNT[menu]):
            transport.globalTransport(midi.FPT_Left, 1)
        for _ in range(_MENU_DOWN_COUNT[item]):
            transport.globalTransport(midi.FPT_Down, 1)