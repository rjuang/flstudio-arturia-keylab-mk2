import _random

import arrangement
import channels

import arturia_leds
import arturia_macros
import arturia_midi
import arturia_playlist
import config
import debug
import general
import midi
import mixer
import patterns
import playlist
import transport
import ui
import utils

from arturia_display import ArturiaDisplay
from arturia_midi import MidiEventDispatcher
from arturia_navigation import NavigationMode
from arturia_leds import ArturiaLights
from macro_actions import Actions

SCRIPT_VERSION = general.getVersion()

if SCRIPT_VERSION >= 8:
    import plugins

# Event code indicating stop event
SS_STOP = 0
# Event code indicating start start event
SS_START = 2


class ArturiaMidiProcessor:
    @staticmethod
    def _is_pressed(event):
        return event.controlVal != 0

    def __init__(self, controller):
        def by_midi_id(event): return event.midiId
        def by_control_num(event): return event.controlNum
        def ignore_release(event): return self._is_pressed(event)

        self._controller = controller
        self._button_hold_action_committed = False
        self._button_mode = 0
        self._locked_mode = 0
        self._random = _random.Random()
        self._mixer_plugins_visible = False
        self._mixer_plugins_last_track = 0

        self._midi_id_dispatcher = (
            MidiEventDispatcher(by_midi_id)
            .SetHandler(144, self.OnCommandEvent)
            .SetHandler(176, self.OnKnobEvent)
            .SetHandler(224, self.OnSliderEvent))   # Sliders 1-9

        self._midi_command_dispatcher = (
            MidiEventDispatcher(by_control_num)
            .SetHandler(91, self.OnTransportsBack)
            .SetHandler(92, self.OnTransportsForward)
            .SetHandler(93, self.OnTransportsStop)
            .SetHandler(94, self.OnTransportsPausePlay)
            .SetHandler(95, self.OnTransportsRecord)
            .SetHandler(86, self.OnTransportsLoop)

            .SetHandler(80, self.OnGlobalSave)
            .SetHandler(87, self.OnGlobalIn, ignore_release)
            .SetHandler(88, self.OnGlobalOut, ignore_release)
            .SetHandler(89, self.OnGlobalMetro, ignore_release)
            .SetHandler(81, self.OnGlobalUndo)

            .SetHandlerForKeys(range(8, 16), self.OnTrackSolo, ignore_release)
            .SetHandlerForKeys(range(16, 24), self.OnTrackMute, ignore_release)
            .SetHandlerForKeys(range(0, 8), self.OnTrackRecord)

            .SetHandler(74, self.OnTrackRead, ignore_release)
            .SetHandler(75, self.OnTrackWrite, ignore_release)

            .SetHandler(98, self.OnNavigationLeft)
            .SetHandler(99, self.OnNavigationRight)
            .SetHandler(84, self.OnNavigationKnobPressed, ignore_release)

            .SetHandler(49, self.OnBankNext)
            .SetHandler(48, self.OnBankPrev)
            .SetHandler(47, self.OnLivePart1, ignore_release)
            .SetHandler(46, self.OnLivePart2, ignore_release)

            .SetHandlerForKeys(range(24, 32), self.OnBankSelect, ignore_release)
            .SetHandlerForKeys(range(104, 112), self.OnStartOrEndSliderEvent)
        )
        self._knob_dispatcher = (
            MidiEventDispatcher(by_control_num)
            .SetHandlerForKeys(range(16, 25), self.OnPanKnobTurned)
            .SetHandler(60, self.OnNavigationKnobTurned)
        )

        def get_volume_line(): return '    [%d%%]' % int(channels.getChannelVolume(channels.selectedChannel()) * 100)
        def get_panning_line(): return '    [%d%%]' % int(channels.getChannelPan(channels.selectedChannel()) * 100)
        def get_pitch_line(): return '    [%d%%]' % int (channels.getChannelPitch(channels.selectedChannel()) * 100)
        def get_pattern_line(): return arturia_playlist.get_playlist_track_name(patterns.patternNumber())
        def get_channel_line(): return '[%s]' % (channels.getChannelName(channels.selectedChannel()))
        def get_plugin_line(): return '[%s]' % channels.getChannelName(channels.selectedChannel())

        def get_playlist_track():
            current_track = arturia_playlist.current_playlist_track()
            name = arturia_playlist.get_playlist_track_name(current_track)
            return '%d: [%s]' % (current_track, name)

        def get_target_mixer_track():
            track = channels.getTargetFxTrack(channels.selectedChannel())
            return '%d' % track if track > 0 else 'MASTER'

        self._navigation = (
            NavigationMode(self._controller.paged_display())
            .AddMode('Channel', self.OnUpdateChannel, self.OnChannelKnobPress, get_channel_line)
            .AddMode('Volume', self.OnUpdateVolume, self.OnVolumeKnobPress, get_volume_line)
            .AddMode('Panning', self.OnUpdatePanning, self.OnPanningKnobPress,  get_panning_line)
        )

        if SCRIPT_VERSION >= 8:
            self._navigation.AddMode('Pitch', self.OnUpdatePitch, self.OnPitchKnobPress, get_pitch_line)

        (self._navigation
            .AddMode('Auto Color', self.OnUpdateChannel, self.OnColorKnobPress, get_channel_line)
            .AddMode('Plugin Preset', self.OnUpdatePlugin, self.OnChannelKnobPress, get_plugin_line)
            .AddMode('Pattern', self.OnUpdatePattern, self.OnPatternKnobPress, get_pattern_line)
            .AddMode('Playlist Track', self.OnUpdatePlaylistTrack, self.OnTrackPlaylistKnobPress, get_playlist_track)
            .AddMode('Target Mix Track', self.OnUpdateTargetMixerTrack, self.OnMixerTrackKnobPress,
                     get_target_mixer_track)
         )
        self._update_focus_time_ms = 0
        self._debug_value = 0
        # Mapping of string -> entry corresponding to scheduled long press task
        self._long_press_tasks = {}
        # Indicates if punch button is pressed (needed for essential keyboards)
        self._punched = False
        # Indicates pad is recording
        self._is_pad_recording = False
        self._macros = arturia_macros.ArturiaMacroBank(display_fn=self._display_hint)

    def circular(self, low, high, x):
        if x > high:
            x = low + (x - high - 1)
        elif x < low:
            x = high - (low - x - 1)
        return x

    def clip(self, low, high, x):
        return max(low, min(high, x))

    def NotifyPadRecordingState(self, is_recording):
        self._is_pad_recording = is_recording

    def OnUpdateVolume(self, delta):
        channel = channels.selectedChannel()
        volume = self.clip(0., 1., channels.getChannelVolume(channels.selectedChannel()) + (delta / 100.0))
        channels.setChannelVolume(channel, volume)

    def OnUpdatePanning(self, delta):
        channel = channels.selectedChannel()
        pan = self.clip(-1., 1., channels.getChannelPan(channel) + (delta / 100.0))
        channels.setChannelPan(channel, pan)

    def OnUpdatePitch(self, delta):
        if SCRIPT_VERSION < 8:
            # This isn't supported in older versions
            return
        channel = channels.selectedChannel()
        pan = self.clip(-1., 1., channels.getChannelPitch(channel) + (delta / 100.0))
        channels.setChannelPitch(channel, pan)

    def OnUpdateTimeMarker(self, delta, power=0):
        num_beats = patterns.getPatternLength(patterns.patternNumber())
        step_size = 1.0 / float(num_beats)
        pos = transport.getSongPos()
        delta *= (2**power)
        transport.setSongPos(self.clip(0.0, 1.0, pos + step_size * delta))

    def OnUpdatePattern(self, delta):
        index = self.clip(1, patterns.patternCount(), patterns.patternNumber() + delta)
        if (config.ENABLE_PATTERN_NAV_WHEEL_CREATE_NEW_PATTERN and
                patterns.patternNumber() + delta > patterns.patternCount()):
            self._new_empty_pattern(linked=False)
        else:
            arturia_playlist.select_playlist_track_from_pattern(index)

    def OnUpdateChannel(self, delta):
        index = self.clip(0, channels.channelCount() - 1, channels.selectedChannel() + delta)
        self._select_one_channel(index)

    def OnVolumeKnobPress(self):
        selected = channels.selectedChannel()
        if selected < 0:
            return
        channels.setChannelVolume(selected, 0.78125)

    def OnPanningKnobPress(self):
        selected = channels.selectedChannel()
        if selected < 0:
            return
        channels.setChannelPan(selected, 0.0)

    def OnPitchKnobPress(self):
        selected = channels.selectedChannel()
        if selected < 0:
            return
        if SCRIPT_VERSION >= 8:
            channels.setChannelPitch(selected, 0)

    def OnColorKnobPress(self):
        selected = channels.selectedChannel()
        if selected < 0:
            return
        rgb = int(self._random.random() * 16777215.0)
        channels.setChannelColor(selected, rgb)
        self._controller.encoders().Refresh()

    def OnChannelKnobPress(self):
        selected = channels.selectedChannel()
        if selected < 0:
            return

        if SCRIPT_VERSION > 9:
            channels.showCSForm(selected, -1)
        elif SCRIPT_VERSION >= 8:
            if plugins.isValid(selected):
                # If valid plugin, then toggle
                channels.showEditor(selected)
            else:
                # For audio, no ability to close window settings
                channels.showCSForm(selected)
        else:
            # Older versions, don't bother with toggle since no support for determining whether plugin or audio
            channels.showCSForm(selected)

    def _toggle_window_visibility(self, window):
        if ui.getVisible(window):
            ui.hideWindow(window)
        else:
            ui.showWindow(window)
            ui.setFocused(window)

    def _toggle_all_mixer_plugins(self):
        mixer_track = channels.getTargetFxTrack(channels.selectedChannel())
        mixer.setTrackNumber(mixer_track)
        # TODO: Section below seems to crash in windows. Consider rate-limiting calls to globalTransport and window
        # fetching. Also possible crash when trying to get caption when no window in focus.
        # if mixer_track != self._mixer_plugins_last_track:
        #    self._mixer_plugins_last_track = mixer_track
        #    self._mixer_plugins_visible = False
        # self._mixer_plugins_visible = ~self._mixer_plugins_visible
        # track_name = "(%s)" % mixer.getTrackName(mixer_track)
        # names = set()
        # while True:
        #    transport.globalTransport(midi.FPT_MixerWindowJog, 1)
        #    window_title = ui.getFocusedFormCaption()
        #    if window_title in names or track_name not in window_title:
        #        break
        #    names.add(window_title)
        # if not self._mixer_plugins_visible:
        #    # Close all windows
        #    while ui.getFocusedFormCaption() in names:
        #        ui.escape()

    def OnPatternKnobPress(self):
        self._toggle_window_visibility(midi.widPianoRoll)

    def OnTrackPlaylistKnobPress(self):
        track_name = playlist.getTrackName(arturia_playlist.current_playlist_track())
        channel_name = channels.getChannelName(channels.selectedChannel())
        track_mode = track_name == channel_name and track_name.startswith('* ')
        if track_mode:
            self.OnChannelKnobPress()
        else:
            self._toggle_window_visibility(midi.widPlaylist)

    def OnMixerTrackKnobPress(self):
        if not channels.getTargetFxTrack(channels.selectedChannel()):
            track = self._next_free_mixer_track()
            self.OnUpdateTargetMixerTrack(track)
        else:
            self._toggle_all_mixer_plugins()

    def OnUnassignedKnobPress(self):
        # TODO
        self._display_hint('Unassigned', 'Knob press')

    def _request_plugin_window_focus(self):
        current_time_ms = ArturiaDisplay.time_ms()
        # Require explicit window focus if last request to focus was more than a second ago.
        if current_time_ms > self._update_focus_time_ms + 1000:
            # This call is expensive so try to use sparingly.
            channels.focusEditor(channels.selectedChannel())
        self._update_focus_time_ms = current_time_ms

    def OnUpdatePlugin(self, delta):
        # Indicator to notify user that preset is in process of being set.
        self._request_plugin_window_focus()
        if SCRIPT_VERSION >= 10:
            idx = channels.selectedChannel()
            if delta > 0:
                plugins.nextPreset(idx)
            elif delta < 0:
                plugins.prevPreset(idx)
        else:
            if delta > 0:
                ui.next()
            elif delta < 0:
                ui.previous()

    def OnUpdateColorRed(self, delta):
        r, g, b = utils.ColorToRGB(channels.getChannelColor(channels.selectedChannel()))
        r = self.clip(0, 255, r + delta)
        channels.setChannelColor(channels.selectedChannel(), utils.RGBToColor(r, g, b))
        self._controller.encoders().Refresh()

    def OnUpdateColorGreen(self, delta):
        r, g, b = utils.ColorToRGB(channels.getChannelColor(channels.selectedChannel()))
        g = self.clip(0, 255, g + delta)
        channels.setChannelColor(channels.selectedChannel(), utils.RGBToColor(r, g, b))
        self._controller.encoders().Refresh()

    def OnUpdateColorBlue(self, delta):
        r, g, b = utils.ColorToRGB(channels.getChannelColor(channels.selectedChannel()))
        b = self.clip(0, 255, b + delta)
        channels.setChannelColor(channels.selectedChannel(), utils.RGBToColor(r, g, b))
        self._controller.encoders().Refresh()

    def _channel_with_route_to_mixer_track(self, track):
        max_channel = channels.channelCount()
        for i in range(max_channel):
            if channels.getTargetFxTrack(i) == track:
                return i
        return -1

    def OnUpdatePlaylistTrack(self, delta):
        track = max(1, min(playlist.trackCount(), arturia_playlist.current_playlist_track() + delta))
        arturia_playlist.set_playlist_track(track)

    def _recolor_mixer_track(self, index):
        if index != 0:
            for i in range(channels.channelCount()):
                if channels.getTargetFxTrack(i) == index:
                    mixer.setTrackColor(index, channels.getChannelColor(i))
                    return
        mixer.setTrackColor(index, -10261391)

    def OnUpdateTargetMixerTrack(self, delta):
        max_track_idx = mixer.trackCount() - 2   # One of the track is a control track
        prev_track = channels.getTargetFxTrack(channels.selectedChannel())
        target_track = self.circular(0, max_track_idx, prev_track + delta)
        # Remember to unset the name of the previous pointed to track.
        mixer.setTrackNumber(target_track, midi.curfxMinimalLatencyUpdate)
        mixer.linkTrackToChannel(midi.ROUTE_ToThis)
        channel_idx = self._channel_with_route_to_mixer_track(prev_track)
        if channel_idx < 0:
            mixer.setTrackName(prev_track, '')
        elif mixer.getTrackName(prev_track) == mixer.getTrackName(target_track):
            mixer.setTrackName(prev_track, arturia_playlist.strip_pattern_name(channels.getChannelName(channel_idx)))
        if target_track == 0:
            mixer.setTrackName(target_track, '')
        if target_track != 0:
            mixer.setTrackNumber(target_track, channels.getChannelColor(channels.selectedChannel()))
        self._recolor_mixer_track(prev_track)

    def ProcessEvent(self, event):
        return self._midi_id_dispatcher.Dispatch(event)

    def OnCommandEvent(self, event):
        self._midi_command_dispatcher.Dispatch(event)

    def OnKnobEvent(self, event):
        self._knob_dispatcher.Dispatch(event)

    def OnSliderEvent(self, event):
        slider_index = event.status - event.midiId
        slider_value = event.controlVal

        if SCRIPT_VERSION < 8:
            # Arturia keyboards on 20.7.2 seem to experience issues with sliders bouncing values between 126 and 127.
            if slider_value >= 126:
                slider_value = 127

        debug.log('OnSliderEvent', 'Slider %d = %d' % (slider_index, slider_value), event=event)
        self._controller.encoders().ProcessSliderInput(event, slider_index, slider_value)

    @staticmethod
    def _get_knob_delta(event):
        val = event.controlVal
        return val if val < 64 else 64 - val

    def _horizontal_scroll(self, delta, power=0):
        if ui.getFocused(midi.widPianoRoll):
            self.OnUpdateTimeMarker(delta, power=power)
        elif ui.getFocused(midi.widPlaylist):
            self.OnUpdateTimeMarker(delta, power=power)
        else:
            transport.globalTransport(midi.FPT_Jog, delta)

    def OnNavigationKnobTurned(self, event):
        delta = self._get_knob_delta(event)
        debug.log('OnNavigationKnob', 'Delta = %d' % delta, event=event)
        if self._button_mode == arturia_macros.SAVE_BUTTON:
            self._change_playlist_track(delta)
        elif self._button_mode or self._locked_mode:
            self._macros.on_macro_actions(self._button_mode | self._locked_mode, arturia_macros.NAV_WHEEL, delta)
            self._button_hold_action_committed = True
        else:
            self._navigation.UpdateValue(delta)

    _KNOB_MAPPING = {
        0: midi.REC_Chan_Plugin_First + 18,
        1: midi.REC_Chan_Plugin_First + 20,
        2: midi.REC_Chan_Plugin_First + 19,
        3: midi.REC_Chan_Plugin_First + 5,
        4: midi.REC_Chan_Plugin_First + 6,
        5: midi.REC_Chan_Plugin_First + 7,
        6: midi.REC_Chan_Plugin_First + 8,
        7: midi.REC_Chan_Plugin_First + 9,
        8: midi.REC_Chan_Plugin_First + 0,
    }

    def OnPanKnobTurned(self, event):
        idx = event.controlNum - 16
        delta = self._get_knob_delta(event)
        self._button_hold_action_committed = True
        if self._button_mode or self._locked_mode:
            macro_id = idx + arturia_macros.ENCODER1
            self._macros.on_macro_actions(self._button_mode | self._locked_mode, macro_id, delta)
        elif self._button_mode == 0:
            self._controller.encoders().ProcessKnobInput(event, idx, delta)

    def OnTransportsBack(self, event):
        debug.log('OnTransportsBack', 'Dispatched', event=event)
        if self._is_pressed(event):
            transport.continuousMove(-1, SS_START)
            self._controller.paged_display().SetActivePage('Time Marker')
        else:
            transport.continuousMove(-1, SS_STOP)
            self._controller.paged_display().SetActivePage('main')

    def OnTransportsForward(self, event):
        debug.log('OnTransportsForward', 'Dispatched', event=event)
        if self._is_pressed(event):
            transport.continuousMove(1, SS_START)
            self._controller.paged_display().SetActivePage('Time Marker')
        else:
            transport.continuousMove(1, SS_STOP)
            self._controller.paged_display().SetActivePage('main')

    def OnTransportsStop(self, event):
        if self._is_pressed(event):
            self._button_mode |= arturia_macros.STOP_BUTTON
            self._button_hold_action_committed = False
            debug.log('OnTransportsStop [down]', 'Dispatched', event=event)
            data1 = arturia_midi.INTER_SCRIPT_DATA1_BTN_DOWN_CMD
        else:
            debug.log('OnTransportsStop [up]', 'Dispatched', event=event)
            data1 = arturia_midi.INTER_SCRIPT_DATA1_BTN_UP_CMD
            self._button_mode &= ~arturia_macros.STOP_BUTTON
            if not self._button_hold_action_committed:
                self._controller.metronome().Reset()
                transport.stop()

        arturia_midi.dispatch_message_to_other_scripts(
            arturia_midi.INTER_SCRIPT_STATUS_BYTE,
            data1,
            event.controlNum)

    def _show_and_focus(self, window):
        ui.showWindow(window)
        ui.setFocused(window)

    def _toggle_visibility(self, window):
        if not ui.getVisible(window):
            ui.showWindow(window)
            ui.setFocused(window)
            return True
        else:
            ui.hideWindow(window)
            return False

    def OnTransportsPausePlay(self, event):
        debug.log('OnTransportsPausePlay', 'Dispatched', event=event)
        if self._is_pressed(event):
            self._button_mode |= arturia_macros.PLAY_BUTTON
            self._button_hold_action_committed = False
        else:
            self._button_mode &= ~arturia_macros.PLAY_BUTTON
            if self._button_hold_action_committed:
                # Update event happened so do not process button release.
                return
            song_mode = transport.getLoopMode() == 1
            if config.ENABLE_PIANO_ROLL_FOCUS_DURING_RECORD_AND_PLAYBACK:
                if song_mode:
                    self._show_and_focus(midi.widPlaylist)
                else:
                    self._show_and_focus(midi.widPianoRoll)
            transport.globalTransport(midi.FPT_Play, midi.FPT_Play, event.pmeFlags)

    def OnTransportsRecord(self, event):
        if self._is_pressed(event):
            debug.log('OnTransportsRecord [down]', 'Dispatched', event=event)
            self._button_mode |= arturia_macros.REC_BUTTON
            self._button_hold_action_committed = False
            arturia_midi.dispatch_message_to_other_scripts(
                arturia_midi.INTER_SCRIPT_STATUS_BYTE,
                arturia_midi.INTER_SCRIPT_DATA1_BTN_DOWN_CMD,
                event.controlNum)
        else:
            # Release event
            self._button_mode &= ~arturia_macros.REC_BUTTON
            arturia_midi.dispatch_message_to_other_scripts(
                arturia_midi.INTER_SCRIPT_STATUS_BYTE,
                arturia_midi.INTER_SCRIPT_DATA1_BTN_UP_CMD,
                event.controlNum)
            if self._button_hold_action_committed:
                # Update event happened so do not process button release.
                return
            debug.log('OnTransportsRecord [up]', 'Dispatched', event=event)
            if not self._is_pad_recording:
                transport.record()

    def OnTransportsLoop(self, event):
        debug.log('OnTransportsLoop', 'Dispatched', event=event)
        if self._is_pressed(event):
            self._button_mode |= arturia_macros.LOOP_BUTTON
            self._button_hold_action_committed = False
        else:
            self._button_mode &= ~arturia_macros.LOOP_BUTTON
            if self._button_hold_action_committed:
                return
            transport.globalTransport(midi.FPT_LoopRecord, midi.FPT_LoopRecord, event.pmeFlags)

    def OnGlobalSave(self, event):
        debug.log('OnGlobalSave', 'Dispatched', event=event)
        if self._is_pressed(event):
            self._button_mode |= arturia_macros.SAVE_BUTTON
            self._button_hold_action_committed = False
        else:
            self._button_mode &= ~arturia_macros.SAVE_BUTTON
            if not self._button_hold_action_committed:
                transport.setLoopMode()

    def OnGlobalIn(self, event):
        if arturia_leds.ESSENTIAL_KEYBOARD:
            if self._punched:
                # Dispatch to punchOut for essential keyboards since essential only has one punch button.
                self.OnGlobalOut(event)
                return
        self._punched = True
        debug.log('OnGlobalIn', 'Dispatched', event=event)
        transport.globalTransport(midi.FPT_PunchIn, midi.FPT_PunchIn, event.pmeFlags)
        self._controller.lights().SetLights({ArturiaLights.ID_GLOBAL_IN: ArturiaLights.LED_ON})

    def OnGlobalOut(self, event):
        debug.log('OnGlobalOut', 'Dispatched', event=event)
        self._punched = False
        transport.globalTransport(midi.FPT_PunchOut, midi.FPT_PunchOut, event.pmeFlags)
        Actions.fl_windows_shortcut("right", ctrl=1)
        Actions.fl_windows_shortcut("left", ctrl=1)

        if arrangement.selectionStart() < 0:
            self._controller.lights().SetLights({ArturiaLights.ID_GLOBAL_IN: ArturiaLights.LED_OFF})

    def OnGlobalMetro(self, event):
        debug.log('OnGlobalMetro', 'Dispatched', event=event)
        transport.globalTransport(midi.FPT_Metronome, midi.FPT_Metronome, event.pmeFlags)

    def OnGlobalUndo(self, event):
        debug.log('OnGlobalUndo', 'Dispatched', event=event)
        self._detect_long_press(event, self.OnGlobalUndoShortPress, self.OnGlobalUndoLongPress)

    def OnGlobalUndoShortPress(self, event):
        debug.log('OnGlobalUndo (short press)', 'Dispatched', event=event)
        transport.globalTransport(midi.FPT_Undo, midi.FPT_Undo, event.pmeFlags)

    def OnGlobalUndoLongPress(self, event):
        debug.log('OnGlobalUndo (long press)', 'Dispatched', event=event)
        # Clear current pattern
        self._show_and_focus(midi.widChannelRack)
        ui.cut()
        self._display_hint('CLEARED ACTIVE', 'CHANNEL PATTERN')

    def OnTrackSolo(self, event):
        debug.log('OnTrackSolo', 'Dispatched', event=event)
        playlist_mode = self._navigation.GetMode() == 'Playlist Track'
        if self._button_mode == arturia_macros.SAVE_BUTTON or playlist_mode:
            current_track = arturia_playlist.current_playlist_track()
            playlist.soloTrack(current_track)
            status = playlist.isTrackSolo(current_track)
            self._display_playlist_track_op_hint("Solo Playlist: %d" % status)
            self._button_hold_action_committed = True
        else:
            channels.soloChannel(channels.selectedChannel())

    def OnTrackMute(self, event):
        debug.log('OnTrackMute', 'Dispatched', event=event)
        playlist_mode = self._navigation.GetMode() == 'Playlist Track'
        if self._button_mode == arturia_macros.SAVE_BUTTON or playlist_mode:
            current_track = arturia_playlist.current_playlist_track()
            playlist.muteTrack(current_track)
            status = playlist.isTrackMuted(current_track)
            self._display_playlist_track_op_hint("Mute Playlist: %d" % status)
            self._button_hold_action_committed = True
        else:
            channels.muteChannel(channels.selectedChannel())

    def _detect_long_press(self, event, short_fn, long_fn, duration_ms=450):
        control_id = event.controlNum
        if self._is_pressed(event):
            task = self._controller.scheduler().ScheduleTask(lambda: long_fn(event), delay=duration_ms)
            self._long_press_tasks[control_id] = task
        else:
            # Release event. Attempt to cancel the scheduled long press task.
            if control_id in self._long_press_tasks and self._controller.scheduler().CancelTask(
                    self._long_press_tasks[control_id]):
                # Dispatch short function press if successfully cancelled the long press.
                short_fn(event)

    def OnTrackRecord(self, event):
        debug.log('OnTrackRecord', 'Dispatched', event=event)
        self._detect_long_press(event, self.OnTrackRecordShortPress, self.OnTrackRecordLongPress)

    def _new_empty_pattern(self, linked=True):
        pattern_id = patterns.patternCount() + 1
        if linked:
            pattern_name = arturia_playlist.next_pattern_name()
            color = channels.getChannelColor(channels.selectedChannel())
            patterns.setPatternName(pattern_id, pattern_name)
            patterns.setPatternColor(pattern_id, color)
        patterns.jumpToPattern(pattern_id)
        patterns.selectPattern(pattern_id, 1)
        return pattern_id

    def _new_pattern_from_selected(self):
        self._show_and_focus(midi.widPianoRoll)
        ui.copy()
        self._new_empty_pattern()
        ui.paste()
        # Hack to fix the pattern shift by moving it to far left most.
        transport.globalTransport(midi.FPT_StripJog, -midi.FromMIDI_Max)
        # Deselect region once we've copied it out.
        transport.globalTransport(midi.FPT_PunchOut, midi.FPT_PunchOut)

    def _clone_active_pattern(self):
        active_channel = channels.selectedChannel()
        self._show_and_focus(midi.widChannelRack)
        channels.selectAll()
        ui.copy()
        self._new_empty_pattern()
        ui.paste()
        self._select_one_channel(active_channel)

    def _next_free_mixer_track(self):
        last_track = 0
        for i in range(channels.channelCount()):
            if i == channels.selectedChannel():
                # Skip the assignment for the channel we are assigning.
                continue
            last_track = max(last_track, channels.getTargetFxTrack(i))
        return last_track + 1

    def OnTrackRecordShortPress(self, event):
        debug.log('OnTrackRecord Short', 'Dispatched', event=event)
        # Piano roll needs to be in focus to determine if a new pattern is needed
        piano_roll_visible = ui.getVisible(midi.widPianoRoll)
        self._show_and_focus(midi.widPianoRoll)
        if arrangement.selectionEnd() > arrangement.selectionStart():
            self._new_pattern_from_selected()
        else:
            self._new_empty_pattern()
        if not piano_roll_visible:
            ui.hideWindow(midi.widPianoRoll)

    def OnTrackRecordLongPress(self, event):
        debug.log('OnTrackRecord Long', 'Dispatched', event=event)
        self._clone_active_pattern()

    def _is_pattern_mode(self):
        return transport.getLoopMode() == 0

    def _display_playlist_track_hint(self):
        self._display_playlist_track_op_hint('Playlist Track')

    def _display_playlist_track_op_hint(self, title):
        track = arturia_playlist.current_playlist_track()
        name = arturia_playlist.get_playlist_track_name(track)
        self._display_hint(title, '%d: %s' % (track, name))

    def _change_playlist_track(self, delta):
        # Adjust track number.
        next = arturia_playlist.current_playlist_track() + delta
        if 0 < next <= playlist.trackCount():
            arturia_playlist.set_playlist_track(next)
        self._display_playlist_track_hint()
        self._button_hold_action_committed = True

    def OnTrackRead(self, event):
        debug.log('OnTrackRead', 'Dispatched', event=event)
        # Move to previous pattern (move up pattern list)
        if self._button_mode == arturia_macros.SAVE_BUTTON:
            # Adjust track number.
            self._change_playlist_track(-1)
        else:
            prev = patterns.patternNumber() - 1
            if prev <= 0:
                return
            arturia_playlist.select_playlist_track_from_pattern(prev)

    def OnTrackWrite(self, event):
        debug.log('OnTrackWrite', 'Dispatched', event=event)
        # Move to next pattern (move down pattern list)
        if self._button_mode == arturia_macros.SAVE_BUTTON:
            # Adjust track number.
            self._change_playlist_track(1)
        else:
            next = patterns.patternNumber() + 1
            if next > patterns.patternCount():
                return
            arturia_playlist.select_playlist_track_from_pattern(next)

    def OnNavigationLeft(self, event):
        if self._is_pressed(event):
            if self._button_mode & arturia_macros.RIGHT_BUTTON:
                ui.escape()
                self._button_hold_action_committed = True
                return

            if self._button_mode == arturia_macros.SAVE_BUTTON:
                # Toggle visibility of mixer panel
                is_visible = self._toggle_visibility(midi.widPianoRoll)
                visible_str = 'VISIBLE' if is_visible else 'HIDDEN'
                self._display_hint(line1='Piano Roll', line2=visible_str)
                self._button_hold_action_committed = True
                return

            self._button_mode |= arturia_macros.LEFT_BUTTON
            self._button_hold_action_committed = False
        else:
            self._button_mode &= ~arturia_macros.LEFT_BUTTON

        if config.ENABLE_NAV_BUTTON_TOGGLE_VISIBILITY:
            self._detect_long_press(event, self.OnNavigationLeftShortPress, self.OnNavigationLeftLongPress,
                                    duration_ms=1000)

    def OnNavigationRight(self, event):
        if self._is_pressed(event):
            if self._button_mode & arturia_macros.LEFT_BUTTON:
                ui.escape()
                self._button_hold_action_committed = True
                return

            if self._button_mode == arturia_macros.SAVE_BUTTON:
                is_visible = self._toggle_visibility(midi.widPlaylist)
                visible_str = 'VISIBLE' if is_visible else 'HIDDEN'
                self._display_hint(line1='Playlist', line2=visible_str)
                self._button_hold_action_committed = True
                return
            self._button_mode |= arturia_macros.RIGHT_BUTTON
            self._button_hold_action_committed = False
        else:
            self._button_mode &= ~arturia_macros.RIGHT_BUTTON

        if config.ENABLE_NAV_BUTTON_TOGGLE_VISIBILITY:
            self._detect_long_press(event, self.OnNavigationRightShortPress, self.OnNavigationRightLongPress,
                                    duration_ms=1000)

    def OnNavigationLeftShortPress(self, event):
        debug.log('OnNavigationLeftShortPress', 'Dispatched', event=event)
        if self._button_hold_action_committed:
            return
        self._navigation.PreviousMode()

    def OnNavigationRightShortPress(self, event):
        debug.log('OnNavigationRightShortPress', 'Dispatched', event=event)
        if self._button_hold_action_committed:
            return
        self._navigation.NextMode()

    def OnNavigationLeftLongPress(self, event):
        debug.log('OnNavigationLeftLongPress', 'Dispatched', event=event)
        if self._button_hold_action_committed:
            return
        # Toggle visibility of channel rack
        is_visible = self._toggle_visibility(midi.widChannelRack)
        visible_str = 'VISIBLE' if is_visible else 'HIDDEN'
        self._controller.lights().SetLights({ArturiaLights.ID_NAVIGATION_LEFT: ArturiaLights.AsOnOffByte(is_visible)})
        self._display_hint(line1='Channel Rack', line2=visible_str)

    def OnNavigationRightLongPress(self, event):
        debug.log('OnNavigationRightLongPress', 'Dispatched', event=event)
        if self._button_hold_action_committed:
            return
        # Toggle visibility of mixer panel
        is_visible = self._toggle_visibility(midi.widMixer)
        visible_str = 'VISIBLE' if is_visible else 'HIDDEN'
        self._controller.lights().SetLights({ArturiaLights.ID_NAVIGATION_RIGHT: ArturiaLights.AsOnOffByte(is_visible)})
        self._display_hint(line1='Mixer Panel', line2=visible_str)

    def OnNavigationKnobPressed(self, event):
        debug.log('OnNavigationKnobPressed', 'Dispatched', event=event)
        self._button_hold_action_committed = True
        was_locked = self._locked_mode
        if self._button_mode & arturia_macros.LOOP_BUTTON:
            self._locked_mode = arturia_macros.LOOP_BUTTON
            self._display_hint('Entering', 'Move Mode')
        elif self._button_mode & arturia_macros.REC_BUTTON:
            self._locked_mode = arturia_macros.REC_BUTTON
            self._display_hint('Entering', 'H. Scroll Mode')
        elif self._button_mode:
            self._locked_mode = self._button_mode
            self._display_hint('Locking', 'Modifier Button')
        else:
            self._locked_mode = 0
            if not was_locked:
                self._navigation.NotifyKnobPressed()
            else:
                self._display_hint('Exiting mode')

    def OnBankNext(self, event):
        self._detect_long_press(event, self.OnBankNextShortPress, self.OnBankNextLongPress)

    def OnBankNextShortPress(self, event):
        debug.log('OnBankNext (short)', 'Dispatched', event=event)
        self._controller.encoders().NextControlsPage()

    def OnBankNextLongPress(self, event):
        debug.log('OnBankNext (long)', 'Dispatched', event=event)
        self.OnLivePart1(event)

    def OnBankPrev(self, event):
        self._detect_long_press(event, self.OnBankPrevShortPress, self.OnBankPrevLongPress)

    def OnBankPrevShortPress(self, event):
        debug.log('OnBankPrev (short)', 'Dispatched', event=event)
        self._controller.encoders().PrevControlsPage()

    def OnBankPrevLongPress(self, event):
        debug.log('OnBankPrev (long)', 'Dispatched', event=event)
        self.OnLivePart2(event)

    def OnLivePart1(self, event):
        debug.log('OnLivePart1', 'Dispatched', event=event)
        self._controller.encoders().ToggleKnobMode()

    def OnLivePart2(self, event):
        debug.log('OnLivePart2', 'Dispatched', event=event)
        self._controller.encoders().ToggleCurrentMode()

    def OnBankSelect(self, event):
        bank_index = event.controlNum - 24
        debug.log('OnBankSelect', 'Selected bank index=%d' % bank_index, event=event)
        if self._button_mode or self._locked_mode:
            debug.log('OnBankSelect', 'Dispatching macro. Mod=%d, index=%d' % (self._button_mode, bank_index),
                      event=event)
            channel_index = self._controller.encoders().GetBankChannelIndex(bank_index)
            self._macros.on_macro_actions(self._button_mode | self._locked_mode, bank_index, channel_index)
            self._button_hold_action_committed = True
        else:
            self._controller.encoders().ProcessBankSelection(event, bank_index)

    def OnStartOrEndSliderEvent(self, event):
        debug.log('OnStartOrEndSliderEvent', 'Dispatched', event=event)
        self._controller.encoders().StartOrEndSliderInput()

    def _display_hint(self, line1=None, line2=None):
        if line1 is None:
            line1 = ' '
        if line2 is None:
            line2 = ' '
        self._controller.paged_display().SetPageLines('hint', line1=line1, line2=line2)
        self._controller.paged_display().SetActivePage('hint', expires=1500)

    def _select_one_channel(self, index):
        if SCRIPT_VERSION >= 8:
            channels.selectOneChannel(index)
        else:
            channels.deselectAll()
            channels.selectChannel(index, 1)
        if config.ENABLE_CONTROLS_FL_HINTS:
            ui.setHintMsg('[%d:%d] %s' % (channels.selectedChannel() + 1, patterns.patternNumber(),
                                          channels.getChannelName(channels.selectedChannel())))
