""" Defines all constants and available actions that can be linked to a macro button. """
import channels
import general
import midi
import patterns
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

# Number of times the up arrow needs to be clicked to reach the menu item.
# NOTE: Do not use "down" arrow because some menus are dynamically populated. Pressing up skips the dynamic portion of
# the menu.
_MENU_UP_COUNT = {
    # View menu
    'playlist': 25,
    'piano roll': 24,
    'channel rack': 23,
    'mixer': 22,
    'browser': 21,
    'project picker': 20,
    'plugin picker': 19,
    'tempo tapper': 18,
    'touch controller': 17,
    'script output': 16,
    'toolbars': 15,
    'tests': 14,
    'plugin performance monitor': 13,
    'close all windows': 12,
    'close all plugin windows': 11,
    'close all unfocused windows': 10,
    'align all channel editors': 9,
    'arrange windows': 8,
    'background': 7,
    'undo history': 6,
    'patterns': 5,
    'generators in use': 4,
    'effects in use': 3,
    'remote control': 2,
    'plugin database': 1,

    # Patterns menu
    'find first empty': 18,
    'find next empty': 17,
    'find next empty (no naming)': 16,
    'select in playlist': 15,
    'rename and color': 14,
    'random color': 13,
    'open in project browser': 12,
    'set time signature': 11,
    'transpose': 10,
    'insert one': 9,
    'clone': 8,
    'delete': 7,
    'move up': 6,
    'move down': 5,
    'split by channel': 4,
    'quick render as audio clip': 3,
    'render as audio clip': 2,
    'render and replace': 1,

    # Tools menu
    'browser smart find': -1,
    'one-click audio recording': -2,
    'macros': -3,
    'riff machine': -4,
    'control creator': -5,

    'next to last tweaked': 1,
    'last tweaked': 2,
    'clear log': 3,
    'dump score log to selected pattern': 4,
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
                Actions._navigate_to_menu('view', 'browser')
                Actions.enter()
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
    def close_all_plugin_windows():
        """Close all plugin"""
        Actions._open_app_menu()
        Actions._navigate_to_menu('view', 'close all plugin windows')
        Actions.enter()

    @staticmethod
    def cycle_active_window():
        """Cycle active win"""
        ui.selectWindow(False)

    @staticmethod
    def name_first_empty_pattern():
        """First empty pat"""
        Actions._open_app_menu()
        Actions._navigate_to_menu('patterns', 'find first empty')
        Actions.enter()

    @staticmethod
    def name_next_empty_pattern():
        """Next empty pat"""
        transport.globalTransport(midi.FPT_F4, 1)

    @staticmethod
    def rename_and_color():
        """Rename & color"""
        transport.globalTransport(midi.FPT_F2, 1)

    @staticmethod
    def toggle_script_output_visibility():
        """Script output"""
        Actions._open_app_menu()
        Actions._navigate_to_menu('view', 'script output')
        Actions.enter()

    @staticmethod
    def clone_pattern():
        """Clone pattern"""
        Actions._open_app_menu()
        Actions._navigate_to_menu('patterns', 'clone')
        Actions.enter()

    @staticmethod
    def enter():
        """Press enter"""
        ui.enter()

    @staticmethod
    def escape():
        """Press escape"""
        ui.escape()

    @staticmethod
    def toggleSnap():
        """Toggle snap"""
        ui.snapOnOff()

    @staticmethod
    def cut():
        """Cut"""
        ui.cut()

    @staticmethod
    def copy():
        """Copy"""
        ui.copy()

    @staticmethod
    def paste():
        """Paste"""
        ui.paste()

    @staticmethod
    def delete():
        """Delete"""
        ui.delete()

    @staticmethod
    def insert():
        """Insert"""
        ui.insert()

    @staticmethod
    def up():
        """Press up"""
        ui.up()

    @staticmethod
    def down():
        """Press down"""
        ui.down()

    @staticmethod
    def left():
        """Press left"""
        ui.left()

    @staticmethod
    def right():
        """Press right"""
        ui.right()

    @staticmethod
    def channel_rack_up():
        """Channelrack up"""
        select = min(max(0, channels.channelNumber() - 1), channels.channelCount() - 1)
        channels.deselectAll()
        channels.selectChannel(select, 1)

    @staticmethod
    def channel_rack_down():
        """Channelrack down"""
        select = min(max(0, channels.channelNumber() + 1), channels.channelCount() - 1)
        channels.deselectAll()
        channels.selectChannel(select, 1)

    @staticmethod
    def start_edison_recording():
        """Start Edison Rec"""
        Actions._open_app_menu()
        Actions._navigate_to_menu('tools', 'one-click audio recording')
        Actions.enter()

    @staticmethod
    def random_pattern_generator():
        """Random pattern"""
        Actions._open_app_menu()
        Actions._navigate_to_menu('tools', 'riff machine')
        Actions.enter()

    @staticmethod
    def toggle_start_on_input():
        """Start on input"""
        transport.globalTransport(midi.FPT_WaitForInput, 1)

    @staticmethod
    def toggle_metronome():
        """Metronome"""
        transport.globalTransport(midi.FPT_Metronome, 1)

    @staticmethod
    def toggle_loop_recording():
        """Loop recording"""
        transport.globalTransport(midi.FPT_LoopRecord, 1)

    @staticmethod
    def toggle_step_edit():
        """Step edit"""
        transport.globalTransport(midi.FPT_StepEdit, 1)

    @staticmethod
    def toggle_start_count():
        """Start Count"""
        transport.globalTransport(midi.FPT_CountDown, 1)

    @staticmethod
    def noop():
        """Not assigned"""
        # Do nothing
        pass

    @staticmethod
    def _open_app_menu():
        # FPT_Menu needs to be triggered when channel rack in focus in order to bring up the app menu.
        # Save the visibility state of the channel rack and restore at the end.
        ui.closeActivePopupMenu()
        channel_rack_visible = ui.getVisible(midi.widChannelRack)
        ui.showWindow(midi.widChannelRack)
        ui.setFocused(midi.widChannelRack)
        transport.globalTransport(midi.FPT_Menu, 1)
        if not channel_rack_visible:
            ui.hideWindow(midi.widChannelRack)
        # Give some time for popup to appear
        time.sleep(0.2)
        timeout_time = time.monotonic() + 1
        # Avoid exceed waiting more than 1 second
        while not ui.isInPopupMenu() and time.monotonic() < timeout_time:
            time.sleep(0.05)

    @staticmethod
    def _navigate_to_menu(menu, item):
        restore_pattern = None
        if menu == 'patterns':
            # Need to jump to first pattern and restore at end
            restore_pattern = patterns. patternNumber()
            patterns.jumpToPattern(1)
        vertical_count = _MENU_UP_COUNT[item]
        vertical_cmd = midi.FPT_Up if vertical_count > 0 else midi.FPT_Down
        for _ in range(_MENU_LEFT_COUNT[menu]):
            transport.globalTransport(midi.FPT_Left, 1)
        for _ in range(abs(vertical_count)):
            transport.globalTransport(vertical_cmd, 1)
        if restore_pattern:
            patterns.jumpToPattern(restore_pattern)
