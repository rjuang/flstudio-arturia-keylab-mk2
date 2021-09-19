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

PYKEYS_ENABLED = False
try:
    import pykeys
    PYKEYS_ENABLED = True
    print('pykeys library enabled')
except Exception as e:
    PYKEYS_ENABLED = False
    print('pykeys unavailable: %s' % e)

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

# Map any additional functions we need to customize to values >= 128
# Value representing when wheel scroll event occurs.
NAV_WHEEL = 128
ENCODER1 = 129
ENCODER2 = 130
ENCODER3 = 131
ENCODER4 = 132
ENCODER5 = 133
ENCODER6 = 134
ENCODER7 = 135
ENCODER8 = 136
ENCODER9 = 137

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

STEPS_PER_BAR = 16


def _ticks_per_step():
    return general.getRecPPQ() / 4


def _ticks_per_bar():
    return STEPS_PER_BAR * _ticks_per_step()


class Actions:
    """Class that houses all action functions available.

    NOTE: Doc-strings are used to document the macro. This allows for a two-button press plus bank button to display
    the doc-string to the user. As such, try to limit doc strings to 16-chars for the help-system implementation.
    """
    RANDOM_GENERATOR = _random.Random()

    # ---------------------- AVAILABLE ACTIONS --------------------------
    @staticmethod
    def toggle_playlist_visibility(unused_param_value):
        """Playlist"""
        transport.globalTransport(midi.FPT_F5, 1)

    @staticmethod
    def toggle_channel_rack_visibility(unused_param_value):
        """Channel Rack"""
        transport.globalTransport(midi.FPT_F6, 1)

    @staticmethod
    def toggle_piano_roll_visibility(unused_param_value):
        """Piano Roll"""
        transport.globalTransport(midi.FPT_F7, 1)

    @staticmethod
    def toggle_mixer_visibility(unused_param_value):
        """Toggle mixer"""
        transport.globalTransport(midi.FPT_F9, 1)

    @staticmethod
    def toggle_browser_visibility(unused_param_value):
        """Toggle browser"""
        if PYKEYS_ENABLED:
            Actions._fl_windows_shortcut('f8', alt=1)
        else:
            if ui.getVisible(midi.widBrowser):
                ui.hideWindow(midi.widBrowser)
            else:
                ui.showWindow(midi.widBrowser)
                ui.setFocused(midi.widBrowser)

    @staticmethod
    def toggle_plugin_visibility(unused_param_value):
        """Toggle plugin"""
        if SCRIPT_VERSION >= 9:
            channels.showCSForm(channels.channelNumber(), -1)
        else:
            channels.focusEditor(channels.channelNumber())

    @staticmethod
    def undo(unused_param_value):
        """Undo"""
        general.undoUp()

    @staticmethod
    def redo(unused_param_value):
        """Redo"""
        general.undoDown()

    @staticmethod
    def close_all_plugin_windows(unused_param_value):
        """Close all plugin"""
        Actions._fl_windows_shortcut('f12', alt=1)

    @staticmethod
    def cycle_active_window(unused_param_value):
        """Cycle active win"""
        ui.selectWindow(False)

    @staticmethod
    def name_first_empty_pattern(unused_param_value):
        """First empty pat"""
        Actions._fl_windows_shortcut('f4', shift=1)

    @staticmethod
    def name_next_empty_pattern(unused_param_value):
        """Next empty pat"""
        transport.globalTransport(midi.FPT_F4, 1)

    @staticmethod
    def rename_and_color(unused_param_value):
        """Rename & color"""
        transport.globalTransport(midi.FPT_F2, 1)

    @staticmethod
    def toggle_script_output_visibility(unused_param_value):
        """Script output"""
        Actions._navigate_to_menu('view')
        Actions._fl_windows_shortcut('s')

    @staticmethod
    def clone_pattern(unused_param_value):
        """Clone pattern"""
        Actions._fl_windows_shortcut('c', ctrl=1, shift=1)

    @staticmethod
    def clone_channel(unused_param_value):
        """Clone channel"""
        ui.setFocused(midi.widChannelRack)
        Actions._fl_windows_shortcut('c', alt=1)

    @staticmethod
    def enter(unused_param_value):
        """Press enter"""
        if PYKEYS_ENABLED:
            Actions._fl_windows_shortcut('return')
        else:
            ui.enter()

    @staticmethod
    def escape(unused_param_value):
        """Press escape"""
        if PYKEYS_ENABLED:
            Actions._fl_windows_shortcut('escape')
        else:
            ui.escape()

    @staticmethod
    def toggle_snap(unused_param_value):
        """Toggle snap"""
        ui.snapOnOff()

    @staticmethod
    def cut(unused_param_value):
        """Cut"""
        ui.cut()

    @staticmethod
    def copy(unused_param_value):
        """Copy"""
        ui.copy()

    @staticmethod
    def paste(unused_param_value):
        """Paste"""
        ui.paste()

    @staticmethod
    def delete(unused_param_value):
        """Delete"""
        ui.delete()

    @staticmethod
    def insert(unused_param_value):
        """Insert"""
        ui.insert()

    @staticmethod
    def up(unused_param_value):
        """Press up"""
        ui.up()

    @staticmethod
    def down(unused_param_value):
        """Press down"""
        ui.down()

    @staticmethod
    def left(unused_param_value):
        """Press left"""
        ui.left()

    @staticmethod
    def right(unused_param_value):
        """Press right"""
        ui.right()

    @staticmethod
    def channel_rack_up(unused_param_value):
        """Channelrack up"""
        select = min(max(0, channels.channelNumber() - 1), channels.channelCount() - 1)
        channels.deselectAll()
        channels.selectChannel(select, 1)

    @staticmethod
    def channel_rack_down(unused_param_value):
        """Channelrack down"""
        select = min(max(0, channels.channelNumber() + 1), channels.channelCount() - 1)
        channels.deselectAll()
        channels.selectChannel(select, 1)

    @staticmethod
    def start_edison_recording(unused_param_value):
        """Start Edison Rec"""
        Actions._navigate_to_menu('tools')
        Actions._fl_windows_shortcut('o')  # One click audio recording
        Actions._fl_windows_shortcut('e')  # Edison

    @staticmethod
    def random_pattern_generator(unused_param_value):
        """Random pattern"""
        Actions._navigate_to_menu('tools')
        Actions._fl_windows_shortcut('r')

    @staticmethod
    def toggle_start_on_input(unused_param_value):
        """Start on input"""
        transport.globalTransport(midi.FPT_WaitForInput, 1)

    @staticmethod
    def toggle_metronome(unused_param_value):
        """Metronome"""
        transport.globalTransport(midi.FPT_Metronome, 1)

    @staticmethod
    def toggle_loop_recording(unused_param_value):
        """Loop recording"""
        transport.globalTransport(midi.FPT_LoopRecord, 1)

    @staticmethod
    def toggle_step_edit(unused_param_value):
        """Step edit"""
        transport.globalTransport(midi.FPT_StepEdit, 1)

    @staticmethod
    def toggle_start_count(unused_param_value):
        """Start Count"""
        transport.globalTransport(midi.FPT_CountDown, 1)

    @staticmethod
    def toggle_overdub(unused_param_value):
        """Toggle Overdub"""
        transport.globalTransport(midi.FPT_Overdub, 1)

    @staticmethod
    def tap_tempo(unused_param_value):
        """Tap tempo"""
        transport.globalTransport(midi.FPT_TapTempo, 1)

    @staticmethod
    def open_menu(unused_param_value):
        """Open menu"""
        transport.globalTransport(midi.FPT_Menu, 1)

    @staticmethod
    def item_menu(unused_param_value):
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
    def sync_all_colors(unused_param_value):
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
    def sync_current_color(unused_param_value):
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
    def random_color(unused_param_value):
        """Random color"""
        selected = channels.selectedChannel()
        if selected < 0:
            return
        rgb = int(Actions.RANDOM_GENERATOR.random() * 16777215.0)
        channels.setChannelColor(selected, rgb)

    @staticmethod
    def rewind_to_beginning(unused_param_value):
        """Rewind to start"""
        transport.setSongPos(0)

    @staticmethod
    def pianoroll_quick_legato(unused_param_value):
        """Quick legato"""
        Actions._fl_windows_shortcut('l', ctrl=1)

    @staticmethod
    def pianoroll_quick_quantize(unused_param_value):
        """Quick quantize"""
        Actions._fl_windows_shortcut('q', ctrl=1)

    @staticmethod
    def pianoroll_quick_quantize_start_times(unused_param_value):
        """Qck quantize start"""
        Actions._fl_windows_shortcut('q', shift=1)

    @staticmethod
    def duplicate(unused_param_value):
        """Duplicate"""
        Actions._fl_windows_shortcut('b', ctrl=1)

    @staticmethod
    def select_all(unused_param_value):
        """Select All"""
        Actions._fl_windows_shortcut('a', ctrl=1)

    @staticmethod
    def deselect_all(unused_param_value):
        """Toggle Select All"""
        Actions._fl_windows_shortcut('d', ctrl=1)

    @staticmethod
    def step_one_step(unused_param_value):
        """Move 1-step"""
        Actions._move_song_pos(1, unit='steps')

    @staticmethod
    def step_back_one_step(unused_param_value):
        """Move 1-step back"""
        Actions._move_song_pos(-1, unit='steps')

    @staticmethod
    def step_one_bar(unused_param_value):
        """Move 1-bar"""
        Actions._move_song_pos(1, unit='bars')

    @staticmethod
    def step_back_one_bar(unused_param_value):
        """Move 1-bar back"""
        Actions._move_song_pos(-1, unit='bars')

    @staticmethod
    def noop(unused_param_value):
        """Not assigned"""
        # Do nothing
        pass

    # ---------------------- ACTIONS FOR KNOBS -----------------------------
    @staticmethod
    def horizontal_zoom(delta):
        """Horizontal zoom"""
        transport.globalTransport(midi.FPT_HZoomJog, delta)
        # Hack to adjust zoom so that it's centered on current time position.
        transport.globalTransport(midi.FPT_Jog, 0)

    @staticmethod
    def vertical_zoom(delta):
        """Vertical zoom"""
        transport.globalTransport(midi.FPT_VZoomJog, delta)

    @staticmethod
    def jog2(delta):
        """Jog2"""
        transport.globalTransport(midi.FPT_Jog2, delta)

    @staticmethod
    def window_jog(delta):
        """Window Jog"""
        delta = 0 if delta < 0 else 1
        transport.globalTransport(midi.FPT_WindowJog, delta)

    @staticmethod
    def mixer_window_jog(delta):
        """Mixer Window Jog"""
        delta = 0 if delta < 0 else 1
        transport.globalTransport(midi.FPT_MixerWindowJog, delta)

    @staticmethod
    def scrub_time_by_bars(delta):
        """Scrub time 1-bar"""
        Actions._move_song_pos(delta, unit='bars')

    @staticmethod
    def scrub_time_by_half_bars(delta):
        """Scrub 1/2 bar"""
        Actions._move_song_pos(STEPS_PER_BAR / 2 * delta, unit='steps')

    @staticmethod
    def scrub_time_by_quarter_bars(delta):
        """Scrub 1/4 bar"""
        Actions._move_song_pos(STEPS_PER_BAR / 4 * delta, unit='steps')

    @staticmethod
    def scrub_time_by_eigth_bars(delta):
        """Scrub 1/8 bar"""
        Actions._move_song_pos(STEPS_PER_BAR / 8 * delta, unit='steps')

    @staticmethod
    def scrub_time_by_steps(delta):
        """Scrub pos 1-step"""
        Actions._move_song_pos(delta, unit='steps')

    @staticmethod
    def scrub_time_by_half_steps(delta):
        """Scrub 1/2 step"""
        Actions._move_song_pos(_ticks_per_step() / 2 * delta, unit='ticks')

    @staticmethod
    def scrub_time_by_quarter_steps(delta):
        """Scrub 1/4 step"""
        Actions._move_song_pos(_ticks_per_step() / 4 * delta, unit='ticks')

    @staticmethod
    def scrub_time_by_eigth_steps(delta):
        """Scrub 1/8 step"""
        Actions._move_song_pos(_ticks_per_step() / 8 * delta, unit='ticks')

    @staticmethod
    def scrub_time_by_sixteenth_steps(delta):
        """Scrub 1/16 step"""
        Actions._move_song_pos(_ticks_per_step() / 16 * delta, unit='ticks')

    @staticmethod
    def scrub_time_by_ticks(delta):
        Actions._move_song_pos(delta, unit='ticks')

    # ---------------------- ACTION TRANSFORMERS  --------------------------
    @staticmethod
    def execute_list(*args_fn, help=None):
        """Combine multiple actions."""
        def _execute_all_fn(unused_param_value):
            for fn in args_fn:
                fn(unused_param_value)
        if help is None and args_fn:
            help = args_fn[0].__doc__
        _execute_all_fn.__doc__ = help
        return _execute_all_fn

    # ---------------------- HELPER METHODS  --------------------------
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
    def _navigate_to_menu(menu):
        Actions._open_app_menu()
        for _ in range(_MENU_LEFT_COUNT[menu]):
            transport.globalTransport(midi.FPT_Left, 1)

    @staticmethod
    def _fl_windows_shortcut(key, shift=0, ctrl=0, alt=0):
        if not PYKEYS_ENABLED:
            return False
        if pykeys.platform() == 'win':
            # FL Studio does not use the win modifier key.
            pykeys.send(key, shift, 0, ctrl, alt)
        else:
            # FL Studio maps the ctrl windows modifier to cmd modifier on macs. Mac version does not use control key.
            pykeys.send(key, shift, ctrl, 0, alt)
        return True

    @staticmethod
    def _move_song_pos(delta, unit='bars'):
        """Move the song position by delta units.

        Params:
            delta: +/- value indicating amount to move the song position by.
            unit: one of 'bars', 'steps', 'ticks
        """
        if unit == 'bars':
            delta_ticks = delta * _ticks_per_bar()
        elif unit == 'steps':
            delta_ticks = delta * _ticks_per_step()
        elif unit == 'ticks':
            delta_ticks = delta
        else:
            raise NotImplementedError('%s is not a supported unit. Must be one of: bars, steps, ticks' % unit)

        current_ticks = transport.getSongPos(midi.SONGLENGTH_ABSTICKS)
        transport.setSongPos(current_ticks + delta_ticks, midi.SONGLENGTH_ABSTICKS)
