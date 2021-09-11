""" Defines all constants and available actions that can be linked to a macro button. """
import _random

import channels
import general
import midi
import mixer
import patterns
import transport
import ui

import time

SCRIPT_VERSION = general.getVersion()

if SCRIPT_VERSION >= 8:
    import plugins

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
# Negative values means use down arrow. This might be needed to avoid dynamically populated menu items.
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

_PIANO_ROLL_ITEM_MENU_DOWN_COUNT = {
    'riff machine': 1,
    'quick legato': 2,
    'articulate': 3,
    'quick quantize': 4,
    'quick quantize start times': 5,
    'quantize': 6,
    'quick chop': 7,
    'chop': 8,
    'glue': 9,
    'apreggiate': 10,
    'strum': 11,
    'flam': 12,
    'claw machine': 13,
    'limit': 14,
    'flip': 15,
    'randomize': 16,
    'scale levels': 17,
    'lfo': 18,
}

_PIANO_ROLL_MENU_DOWN_COUNT = {
    'file': -2,
    'edit': -1,
    'tools': 0,
    'stamp': 1,
    'view': 2,
    'snap': 3,
    'select': 4,
    'group': 5,
    'zoom': 6,
    'time markers': 7,
    'target channel': 8,
    'target control': 9,
    'auto smoothing': 10,
    'preview notes during playback': 11,
    'center': 12,
    'detached': 13,
    'pencil tool': -11,
    'paint tool': -10,
    'paint sequence tool': -9,
    'delete tool': -8,
    'mute tool': -7,
    'slice tool': -6,
    'select tool': -5,
    'zoom tool': -4,
    'playback tool': -3,

    # Edit menu
    'cut': 1,
    'copy': 2,
    'paste': 3,
    'duplicate': 4,
    'delete': 5,
    'shift left': 6,
    'shift right': 7,
    'rotate left': 8,
    'rotate right': 9,
    'transpose up': 10,
    'transpose down': 11,
    'transpose one octave up': 12,
    'transpose one octave down': 13,
    'discard lengths': 14,
    'allow resizing from left': 15,
    'change color': 16,
    'mute': 17,
    'unmute': 18,

     # Select menu
    'select all': 1,
}

_PLAYLIST_MENU_DOWN_COUNT = {

    'detached': -1,
    'pencil tool': 1,
    'paint tool': 2,
    'delete tool': 3,
    'mute tool': 4,
    'slip tool': 5,
    'slice tool': 6,
    'select tool': 7,
    'zoom tool': 8,
    'playback tool': 9,
    'edit': 10,
    'tools': 11,
    'view': 12,
    'snap': 13,
    'select': 14,
    'group': 15,
    'zoom': 16,
    'time markers': 17,
    'picker panel': 18,
    'current clip source': 19,
    'performance mode': 20,

    # Edit menu
    'cut': 1,
    'copy': 2,
    'paste': 3,
    'duplicate': 4,
    'delete': 5,
    'shift left': 6,
    'shift right': 7,
    'rotate left': 8,
    'rotate right': 9,
    'transpose up': 10,
    'transpose down': 11,
    'transpose one octave up': 12,
    'transpose one octave down': 13,
    'discard lengths': 14,
    'allow resizing from left': 15,
    'change color': 16,
    'mute': 17,
    'unmute': 18,

    # Select menu
    'select all': 1,
}


class Actions:
    """Class that houses all action functions available.

    TODO: Doc-strings might be able to be used to document the macro. This could be used to allow for a two-button press
    plus bank button to display the doc-string to the user. As such, try to limit doc strings to 16-chars for future
    help-system implementation.
    """

    RANDOM_GENERATOR = _random.Random()

    # ---------------------- AVAILABLE ACTIONS --------------------------
    @staticmethod
    def toggle_playlist_visibility(channel_index):
        """Playlist"""
        transport.globalTransport(midi.FPT_F5, 1)

    @staticmethod
    def toggle_channel_rack_visibility(channel_index):
        """Channel Rack"""
        transport.globalTransport(midi.FPT_F6, 1)

    @staticmethod
    def toggle_piano_roll_visibility(channel_index):
        """Piano Roll"""
        transport.globalTransport(midi.FPT_F7, 1)

    @staticmethod
    def toggle_mixer_visibility(channel_index):
        """Toggle mixer"""
        transport.globalTransport(midi.FPT_F9, 1)

    @staticmethod
    def toggle_browser_visibility(channel_index):
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
                Actions._enter()
            else:
                ui.showWindow(midi.widBrowser)
                ui.setFocused(midi.widBrowser)

    @staticmethod
    def toggle_plugin_visibility(channel_index):
        """Toggle plugin"""
        if SCRIPT_VERSION >= 9:
            channels.showCSForm(channels.channelNumber(), -1)
        else:
            channels.focusEditor(channels.channelNumber())

    @staticmethod
    def undo(channel_index):
        """Undo"""
        general.undoUp()

    @staticmethod
    def redo(channel_index):
        """Redo"""
        general.undoDown()

    @staticmethod
    def close_all_plugin_windows(channel_index):
        """Close all plugin"""
        Actions._open_app_menu()
        Actions._navigate_to_menu('view', 'close all plugin windows')
        Actions._enter()

    @staticmethod
    def cycle_active_window(channel_index):
        """Cycle active win"""
        ui.selectWindow(False)

    @staticmethod
    def name_first_empty_pattern(channel_index):
        """First empty pat"""
        Actions._open_app_menu()
        Actions._navigate_to_menu('patterns', 'find first empty')
        Actions._enter()

    @staticmethod
    def name_next_empty_pattern(channel_index):
        """Next empty pat"""
        transport.globalTransport(midi.FPT_F4, 1)

    @staticmethod
    def rename_and_color(channel_index):
        """Rename & color"""
        transport.globalTransport(midi.FPT_F2, 1)

    @staticmethod
    def toggle_script_output_visibility(channel_index):
        """Script output"""
        Actions._open_app_menu()
        Actions._navigate_to_menu('view', 'script output')
        Actions._enter()

    @staticmethod
    def clone_pattern(channel_index):
        """Clone pattern"""
        Actions._open_app_menu()
        Actions._navigate_to_menu('patterns', 'clone')
        Actions._enter()

    @staticmethod
    def enter(channel_index):
        """Press enter"""
        ui.enter()

    @staticmethod
    def escape(channel_index):
        """Press escape"""
        ui.escape()

    @staticmethod
    def toggleSnap(channel_index):
        """Toggle snap"""
        ui.snapOnOff()

    @staticmethod
    def cut(channel_index):
        """Cut"""
        ui.cut()

    @staticmethod
    def copy(channel_index):
        """Copy"""
        ui.copy()

    @staticmethod
    def paste(channel_index):
        """Paste"""
        ui.paste()

    @staticmethod
    def delete(channel_index):
        """Delete"""
        ui.delete()

    @staticmethod
    def insert(channel_index):
        """Insert"""
        ui.insert()

    @staticmethod
    def up(channel_index):
        """Press up"""
        ui.up()

    @staticmethod
    def down(channel_index):
        """Press down"""
        ui.down()

    @staticmethod
    def left(channel_index):
        """Press left"""
        ui.left()

    @staticmethod
    def right(channel_index):
        """Press right"""
        ui.right()

    @staticmethod
    def channel_rack_up(channel_index):
        """Channelrack up"""
        select = min(max(0, channels.channelNumber() - 1), channels.channelCount() - 1)
        channels.deselectAll()
        channels.selectChannel(select, 1)

    @staticmethod
    def channel_rack_down(channel_index):
        """Channelrack down"""
        select = min(max(0, channels.channelNumber() + 1), channels.channelCount() - 1)
        channels.deselectAll()
        channels.selectChannel(select, 1)

    @staticmethod
    def start_edison_recording(channel_index):
        """Start Edison Rec"""
        Actions._open_app_menu()
        Actions._navigate_to_menu('tools', 'one-click audio recording')
        Actions.enter()

    @staticmethod
    def random_pattern_generator(channel_index):
        """Random pattern"""
        Actions._open_app_menu()
        Actions._navigate_to_menu('tools', 'riff machine')
        Actions.enter()

    @staticmethod
    def toggle_start_on_input(channel_index):
        """Start on input"""
        transport.globalTransport(midi.FPT_WaitForInput, 1)

    @staticmethod
    def toggle_metronome(channel_index):
        """Metronome"""
        transport.globalTransport(midi.FPT_Metronome, 1)

    @staticmethod
    def toggle_loop_recording(channel_index):
        """Loop recording"""
        transport.globalTransport(midi.FPT_LoopRecord, 1)

    @staticmethod
    def toggle_step_edit(channel_index):
        """Step edit"""
        transport.globalTransport(midi.FPT_StepEdit, 1)

    @staticmethod
    def toggle_start_count(channel_index):
        """Start Count"""
        transport.globalTransport(midi.FPT_CountDown, 1)

    @staticmethod
    def toggle_overdub(channel_index):
        """Toggle Overdub"""
        transport.globalTransport(midi.FPT_Overdub, 1)

    @staticmethod
    def tap_tempo(channel_index):
        """Tap tempo"""
        transport.globalTransport(midi.FPT_TapTempo, 1)

    @staticmethod
    def open_menu(channel_index):
        """Open menu"""
        transport.globalTransport(midi.FPT_Menu, 1)

    @staticmethod
    def item_menu(channel_index):
        """Item menu"""
        transport.globalTransport(midi.FPT_ItemMenu, 1)

    @staticmethod
    def open_mixer_plugin(channel_index):
        """Open mixer plugin"""
        if SCRIPT_VERSION < 8:
            return Actions.noop
        mixer_track_index = channel_index + 1
        mixer.setTrackNumber(mixer_track_index, midi.curfxScrollToMakeVisible)
        for i in range(Actions._num_effects(mixer_track_index)):
            transport.globalTransport(midi.FPT_MixerWindowJog, 1)

    @staticmethod
    def sync_all_colors(channel_index):
        """Sync all colors"""
        num_channels = channels.channelCount()
        for i in range(num_channels):
            color = channels.getChannelColor(i)
            mixer_index = channels.getTargetFxTrack(i)
            if mixer_index <= 0:
                # Nothing to sync
                continue
            mixer.setTrackColor(mixer_index, color)

    @staticmethod
    def sync_current_color(channel_index):
        """Sync channel color"""
        selected = channels.selectedChannel()
        if selected < 0:
            return
        mixer_index = channels.getTargetFxTrack(selected)
        if mixer_index <= 0:
            return
        color = channels.getChannelColor(selected)
        mixer.setTrackColor(mixer_index, color)

    @staticmethod
    def random_color(channel_index):
        """Random color"""
        selected = channels.selectedChannel()
        if selected < 0:
            return
        rgb = int(Actions.RANDOM_GENERATOR.random() * 16777215.0)
        channels.setChannelColor(selected, rgb)

    @staticmethod
    def rewind_to_beginning(channel_index):
        """Rewind to start"""
        transport.setSongPos(0)

    @staticmethod
    def pianoroll_quick_legato(channel_index):
        """Quick legato"""
        Actions._pianoroll_item_menu('quick legato')

    @staticmethod
    def pianoroll_quick_quantize(channel_index):
        """Quick quantize"""
        Actions._pianoroll_item_menu('quick quantize')

    @staticmethod
    def pianoroll_quick_quantize_start_times(channel_index):
        """Qck quantize start"""
        Actions._pianoroll_item_menu('quick quantize start times')

    @staticmethod
    def pianoroll_duplicate(channel_index):
        """Duplicate pianoroll"""
        if ui.getFocused(midi.widPianoRoll) and ui.getVisible(midi.widPianoRoll):
            Actions._pianoroll_menu('edit', 'duplicate')

    @staticmethod
    def playlist_duplicate(channel_index):
        """Duplicate playlist"""
        if ui.getFocused(midi.widPlaylist) and ui.getVisible(midi.widPlaylist):
            Actions._playlist_menu('edit', 'duplicate')

    @staticmethod
    def duplicate(channel_index):
        """Duplicate"""
        if ui.getFocused(midi.widPlaylist) and ui.getVisible(midi.widPlaylist):
            Actions._playlist_menu('edit', 'duplicate')
        else:
            Actions._pianoroll_menu('edit', 'duplicate')

    @staticmethod
    def toggle_select_all(channel_index):
        """Toggle Select All"""
        if ui.getFocused(midi.widPlaylist) and ui.getVisible(midi.widPlaylist):
            Actions._playlist_menu('select', 'select all')
        elif ui.getFocused(midi.widPianoRoll) and ui.getVisible(midi.widPianoRoll):
            Actions._pianoroll_menu('select', 'select all')

    @staticmethod
    def noop(channel_index):
        """Not assigned"""
        # Do nothing
        pass

    # ---------------------- ACTION TRANSFORMERS  --------------------------
    @staticmethod
    def execute_list(*args_fn, help=None):
        """Combine multiple actions."""
        def _execute_all_fn(channel_index):
            for fn in args_fn:
                fn(channel_index)
        if help is None and args_fn:
            help = args_fn[0].__doc__
        _execute_all_fn.__doc__ = help
        return _execute_all_fn

    # ---------------------- HELPER METHODS  --------------------------
    @staticmethod
    def _enter():
        """Press enter"""
        ui.enter()

    @staticmethod
    def _num_effects(mixer_track_index):
        cnt = 0
        for i in range(10):
            try:
                if plugins.isValid(mixer_track_index, i):
                    cnt += 1
            except:
                pass
        return cnt

    @staticmethod
    def _open_app_menu():
        # FPT_Menu needs to be triggered when channel rack in focus in order to bring up the app menu.
        # Save the visibility state of the channel rack and restore at the end.
        ui.closeActivePopupMenu()
        channel_rack_visible = ui.getVisible(midi.widChannelRack)
        # Need to reset focus state of channel rack to ensure menu brought up
        ui.hideWindow(midi.widChannelRack)
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

    @staticmethod
    def _pianoroll_item_menu(item):
        ui.closeActivePopupMenu()
        last_visible = ui.getVisible(midi.widPianoRoll)
        # Need to reset focus state of piano roll to ensure item menu brought up
        ui.hideWindow(midi.widPianoRoll)
        ui.showWindow(midi.widPianoRoll)
        ui.setFocused(midi.widPianoRoll)

        transport.globalTransport(midi.FPT_ItemMenu, 1)
        time.sleep(0.2)
        for _ in range(_PIANO_ROLL_ITEM_MENU_DOWN_COUNT[item]):
            transport.globalTransport(midi.FPT_Down, 1)
        Actions._enter()

        if not last_visible:
            ui.hideWindow(midi.widPianoRoll)

    @staticmethod
    def _pianoroll_menu(menu, item):
        ui.closeActivePopupMenu()
        last_visible = ui.getVisible(midi.widPianoRoll)
        # Need to reset focus state of piano roll to ensure item menu brought up
        if not ui.getFocused(midi.widPianoRoll) or not last_visible:
            ui.hideWindow(midi.widPianoRoll)
            ui.showWindow(midi.widPianoRoll)
            ui.setFocused(midi.widPianoRoll)
        # Force copy so that item in clipboard.
        ui.copy()
        transport.globalTransport(midi.FPT_Menu, 1)
        time.sleep(0.2)
        transport.globalTransport(midi.FPT_Left, 1)
        vertical_count = _PIANO_ROLL_MENU_DOWN_COUNT[menu]
        vertical_cmd = midi.FPT_Down if vertical_count > 0 else midi.FPT_Up
        for _ in range(abs(vertical_count)):
            transport.globalTransport(vertical_cmd, 1)
        ui.right()
        time.sleep(0.2)
        vertical_count = _PIANO_ROLL_MENU_DOWN_COUNT[item]
        vertical_cmd = midi.FPT_Down if vertical_count > 0 else midi.FPT_Up
        for _ in range(abs(vertical_count)):
            transport.globalTransport(vertical_cmd, 1)
        Actions._enter()
        if not last_visible:
            time.sleep(1)
            ui.hideWindow(midi.widPianoRoll)

    @staticmethod
    def _playlist_menu(menu, item):
        ui.closeActivePopupMenu()
        last_visible = ui.getVisible(midi.widPlaylist)
        # Need to reset focus state of piano roll to ensure item menu brought up
        if not ui.getFocused(midi.widPlaylist) or not last_visible:
            ui.hideWindow(midi.widPlaylist)
            ui.showWindow(midi.widPlaylist)
            ui.setFocused(midi.widPlaylist)
        # Force copy so that item in clipboard.
        ui.copy()
        transport.globalTransport(midi.FPT_Menu, 1)
        time.sleep(0.2)
        vertical_count = _PLAYLIST_MENU_DOWN_COUNT[menu]
        vertical_cmd = midi.FPT_Down if vertical_count > 0 else midi.FPT_Up
        for _ in range(abs(vertical_count)):
            transport.globalTransport(vertical_cmd, 1)
        ui.right()
        time.sleep(0.2)
        vertical_count = _PLAYLIST_MENU_DOWN_COUNT[item]
        vertical_cmd = midi.FPT_Down if vertical_count > 0 else midi.FPT_Up
        for _ in range(abs(vertical_count)):
            transport.globalTransport(vertical_cmd, 1)
        Actions._enter()
        if not last_visible:
            ui.hideWindow(midi.widPianoRoll)
