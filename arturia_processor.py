import arrangement
import channels

import arturia_leds
import arturia_midi
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
from arturia_encoders import ArturiaInputControls
from arturia_midi import MidiEventDispatcher
from arturia_navigation import NavigationMode
from arturia_leds import ArturiaLights

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
            .SetHandler(94, self.OnTransportsPausePlay, ignore_release)
            .SetHandler(95, self.OnTransportsRecord)
            .SetHandler(86, self.OnTransportsLoop, ignore_release)

            .SetHandler(80, self.OnGlobalSave, ignore_release)
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
        def get_time_position(): return ' [%d:%d:%d]' % (playlist.getVisTimeBar(), playlist.getVisTimeTick(), playlist.getVisTimeStep())
        def get_pattern_line(): return patterns.getPatternName(patterns.patternNumber())
        def get_channel_line(): return '[%s]' % (channels.getChannelName(channels.selectedChannel()))
        def get_plugin_line(): return '[%s]' % channels.getChannelName(channels.selectedChannel())

        def get_color_red_line():
            r, g, b = utils.ColorToRGB(channels.getChannelColor(channels.selectedChannel()))
            return '[%3d] %3d  %3d ' % (r, g, b)

        def get_color_green_line():
            r, g, b = utils.ColorToRGB(channels.getChannelColor(channels.selectedChannel()))
            return ' %3d [%3d] %3d ' % (r, g, b)

        def get_color_blue_line():
            r, g, b = utils.ColorToRGB(channels.getChannelColor(channels.selectedChannel()))
            return ' %3d  %3d [%3d]' % (r, g, b)

        def get_target_mixer_track():
            track = channels.getTargetFxTrack(channels.selectedChannel())
            return '%d' % track if track > 0 else 'MASTER'

        self._navigation = (
            NavigationMode(self._controller.paged_display())
            .AddMode('Volume', self.OnUpdateVolume, get_volume_line)
            .AddMode('Panning', self.OnUpdatePanning, get_panning_line)
            .AddMode('Pitch', self.OnUpdatePitch, get_pitch_line)
            .AddMode('Time Marker', self.OnUpdateTimeMarker, get_time_position)
            # TODO: Combine RED/GREEN/BLUE to a single preset
            .AddMode('Red Color', self.OnUpdateColorRed, get_color_red_line)
            .AddMode('Green Color', self.OnUpdateColorGreen, get_color_green_line)
            .AddMode('Blue Color',  self.OnUpdateColorBlue, get_color_blue_line)
            .AddMode('Target Mix Track', self.OnUpdateTargetMixerTrack, get_target_mixer_track)
            .AddMode('Channel', self.OnUpdateChannel, get_channel_line)
            .AddMode('Pattern', self.OnUpdatePattern, get_pattern_line)
            .AddMode('Plugin Preset', self.OnUpdatePlugin, get_plugin_line)
        )
        self._update_focus_time_ms = 0
        self._debug_value = 0
        # Mapping of string -> entry corresponding to scheduled long press task
        self._long_press_tasks = {}
        # Indicates if punch button is pressed (needed for essential keyboards)
        self._punched = False

    def circular(self, low, high, x):
        if x > high:
            x = low + (x - high - 1)
        elif x < low:
            x = high - (low - x - 1)
        return x

    def clip(self, low, high, x):
        return max(low, min(high, x))

    def OnUpdateVolume(self, delta):
        channel = channels.selectedChannel()
        volume = self.clip(0., 1., channels.getChannelVolume(channels.selectedChannel()) + (delta / 100.0))
        channels.setChannelVolume(channel, volume)

    def OnUpdatePanning(self, delta):
        channel = channels.selectedChannel()
        pan = self.clip(-1., 1., channels.getChannelPan(channel) + (delta / 100.0))
        channels.setChannelPan(channel, pan)

    def OnUpdatePitch(self, delta):
        channel = channels.selectedChannel()
        pan = self.clip(-1., 1., channels.getChannelPitch(channel) + (delta / 100.0))
        channels.setChannelPitch(channel, pan)

    def OnUpdateTimeMarker(self, delta):
        num_beats = patterns.getPatternLength(patterns.patternNumber())
        step_size = 1.0 / float(num_beats)
        pos = transport.getSongPos()
        transport.setSongPos(self.clip(0.0, 1.0, pos + step_size * delta))

    def OnUpdatePattern(self, delta):
        index = self.clip(1, patterns.patternCount(), patterns.patternNumber() + delta)
        patterns.jumpToPattern(index)

    def OnUpdateChannel(self, delta):
        index = self.clip(0, channels.channelCount() - 1, channels.selectedChannel() + delta)
        channels.selectOneChannel(index)

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
        if delta > 0:
            ui.next()
        elif delta < 0:
            ui.previous()

    def OnUpdateColorRed(self, delta):
        r, g, b = utils.ColorToRGB(channels.getChannelColor(channels.selectedChannel()))
        r = self.clip(0, 255, r + delta)
        channels.setChannelColor(channels.selectedChannel(), utils.RGBToColor(r, g, b))

    def OnUpdateColorGreen(self, delta):
        r, g, b = utils.ColorToRGB(channels.getChannelColor(channels.selectedChannel()))
        g = self.clip(0, 255, g + delta)
        channels.setChannelColor(channels.selectedChannel(), utils.RGBToColor(r, g, b))

    def OnUpdateColorBlue(self, delta):
        r, g, b = utils.ColorToRGB(channels.getChannelColor(channels.selectedChannel()))
        b = self.clip(0, 255, b + delta)
        channels.setChannelColor(channels.selectedChannel(), utils.RGBToColor(r, g, b))

    def _channel_with_route_to_mixer_track(self, track):
        max_channel = channels.channelCount()
        for i in range(max_channel):
            if channels.getTargetFxTrack(i) == track:
                return i
        return -1

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
            mixer.setTrackName(prev_track, channels.getChannelName(channel_idx))
        if target_track == 0:
            mixer.setTrackName(target_track, '')

    def ProcessEvent(self, event):
        return self._midi_id_dispatcher.Dispatch(event)

    def OnCommandEvent(self, event):
        self._midi_command_dispatcher.Dispatch(event)

    def OnKnobEvent(self, event):
        event.handled = False
        self._knob_dispatcher.Dispatch(event)

    def OnSliderEvent(self, event):
        event.handled = False
        slider_index = event.status - event.midiId
        slider_value = event.controlVal

        debug.log('OnSliderEvent', 'Slider %d = %d' % (slider_index, slider_value), event=event)
        self._controller.encoders().ProcessSliderInput(slider_index, slider_value)

    @staticmethod
    def _get_knob_delta(event):
        val = event.controlVal
        return val if val < 64 else 64 - val

    def OnNavigationKnobTurned(self, event):
        delta = self._get_knob_delta(event)
        debug.log('OnNavigationKnob', 'Delta = %d' % delta, event=event)
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
        self._controller.encoders().ProcessKnobInput(idx, delta)

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
            debug.log('OnTransportsStop [down]', 'Dispatched', event=event)
            self._controller.metronome().Reset()
            transport.stop()
            data1 = arturia_midi.INTER_SCRIPT_DATA1_BTN_DOWN_CMD
        else:
            debug.log('OnTransportsStop [up]', 'Dispatched', event=event)
            data1 = arturia_midi.INTER_SCRIPT_DATA1_BTN_UP_CMD

        arturia_midi.dispatch_message_to_other_scripts(
            arturia_midi.INTER_SCRIPT_STATUS_BYTE,
            data1,
            event.controlNum)

    def _show_and_focus(self, window):
        if not ui.getVisible(window):
            ui.showWindow(window)
        if not ui.getFocused(window):
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
        song_mode = transport.getLoopMode() == 1
        if song_mode:
            self._show_and_focus(midi.widPlaylist)
        else:
            self._show_and_focus(midi.widPianoRoll)
        transport.globalTransport(midi.FPT_Play, midi.FPT_Play, event.pmeFlags)

    def OnTransportsRecord(self, event):
        if self._is_pressed(event):
            debug.log('OnTransportsRecord [down]', 'Dispatched', event=event)
            transport.record()
            arturia_midi.dispatch_message_to_other_scripts(
                arturia_midi.INTER_SCRIPT_STATUS_BYTE,
                arturia_midi.INTER_SCRIPT_DATA1_BTN_DOWN_CMD,
                event.controlNum)
        else:
            debug.log('OnTransportsRecord [up]', 'Dispatched', event=event)
            arturia_midi.dispatch_message_to_other_scripts(
                arturia_midi.INTER_SCRIPT_STATUS_BYTE,
                arturia_midi.INTER_SCRIPT_DATA1_BTN_UP_CMD,
                event.controlNum)

    def OnTransportsLoop(self, event):
        debug.log('OnTransportsLoop', 'Dispatched', event=event)
        transport.globalTransport(midi.FPT_LoopRecord, midi.FPT_LoopRecord, event.pmeFlags)

    def OnGlobalSave(self, event):
        debug.log('OnGlobalSave', 'Dispatched', event=event)
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
        channels.soloChannel(channels.selectedChannel())

    def OnTrackMute(self, event):
        debug.log('OnTrackMute', 'Dispatched', event=event)
        channels.muteChannel(channels.selectedChannel())

    def _detect_long_press(self, event, short_fn, long_fn):
        control_id = event.controlNum
        if self._is_pressed(event):
            task = self._controller.scheduler().ScheduleTask(lambda: long_fn(event), delay=450)
            self._long_press_tasks[control_id] = task
        else:
            # Release event. Attempt to cancel the scheduled long press task.
            if self._controller.scheduler().CancelTask(self._long_press_tasks[control_id]):
                # Dispatch short function press if successfully cancelled the long press.
                short_fn(event)

    def OnTrackRecord(self, event):
        debug.log('OnTrackRecord', 'Dispatched', event=event)
        self._detect_long_press(event, self.OnTrackRecordShortPress, self.OnTrackRecordLongPress)

    def _new_empty_pattern(self):
        pattern_id = patterns.patternCount() + 1
        patterns.setPatternName(pattern_id, 'Pattern %d' % pattern_id)
        patterns.jumpToPattern(pattern_id)
        patterns.selectPattern(pattern_id, 1)
        return pattern_id

    def _new_pattern_from_selected(self):
        self._show_and_focus(midi.widPianoRoll)
        ui.copy()
        self._new_empty_pattern()
        ui.paste()

    def _clone_active_pattern(self):
        active_channel = channels.selectedChannel()
        self._show_and_focus(midi.widChannelRack)
        channels.selectAll()
        ui.copy()
        self._new_empty_pattern()
        ui.paste()
        channels.selectOneChannel(active_channel)

    def OnTrackRecordShortPress(self, event):
        debug.log('OnTrackRecord Short', 'Dispatched', event=event)
        if arrangement.selectionEnd() > arrangement.selectionStart():
            self._new_pattern_from_selected()
        else:
            self._new_empty_pattern()

    def OnTrackRecordLongPress(self, event):
        debug.log('OnTrackRecord Long', 'Dispatched', event=event)
        self._clone_active_pattern()

    def OnTrackRead(self, event):
        debug.log('OnTrackRead', 'Dispatched', event=event)
        # Move to previous pattern (move up pattern list)
        prev = patterns.patternNumber() - 1
        if prev <= 0:
            return
        patterns.jumpToPattern(prev)

    def OnTrackWrite(self, event):
        debug.log('OnTrackWrite', 'Dispatched', event=event)
        # Move to next pattern (move down pattern list)
        next = patterns.patternNumber() + 1
        if next > patterns.patternCount():
            return
        patterns.jumpToPattern(next)

    def OnNavigationLeft(self, event):
        self._detect_long_press(event, self.OnNavigationLeftShortPress, self.OnNavigationLeftLongPress)

    def OnNavigationRight(self, event):
        self._detect_long_press(event, self.OnNavigationRightShortPress, self.OnNavigationRightLongPress)

    def OnNavigationLeftShortPress(self, event):
        debug.log('OnNavigationLeftShortPress', 'Dispatched', event=event)
        self._navigation.PreviousMode()

    def OnNavigationRightShortPress(self, event):
        debug.log('OnNavigationRightShortPress', 'Dispatched', event=event)
        self._navigation.NextMode()

    def OnNavigationLeftLongPress(self, event):
        debug.log('OnNavigationLeftLongPress', 'Dispatched', event=event)
        # Toggle visibility of channel rack
        is_visible = self._toggle_visibility(midi.widChannelRack)
        visible_str = 'VISIBLE' if is_visible else 'HIDDEN'
        self._controller.lights().SetLights({ArturiaLights.ID_NAVIGATION_LEFT: ArturiaLights.AsOnOffByte(is_visible)})
        self._display_hint(line1='Channel Rack', line2=visible_str)

    def OnNavigationRightLongPress(self, event):
        debug.log('OnNavigationRightLongPress', 'Dispatched', event=event)
        # Toggle visibility of mixer panel
        is_visible = self._toggle_visibility(midi.widMixer)
        visible_str = 'VISIBLE' if is_visible else 'HIDDEN'
        self._controller.lights().SetLights({ArturiaLights.ID_NAVIGATION_RIGHT: ArturiaLights.AsOnOffByte(is_visible)})
        self._display_hint(line1='Mixer Panel', line2=visible_str)

    def OnNavigationKnobPressed(self, event):
        debug.log('OnNavigationKnobPressed', 'Dispatched', event=event)
        ## DEBUG ONLY ##
        transport.globalTransport(midi.FPT_F8, midi.FPT_F8)
        debug.log('DEBUG', 'Trying to show editor for %d' % channels.channelCount())

    def OnBankNext(self, event):
        self._detect_long_press(event, self.OnBankNextShortPress, self.OnBankNextLongPress)

    def OnBankNextShortPress(self, event):
        debug.log('OnBankNext (short)', 'Dispatched', event=event)
        self._controller.encoders().NextKnobsPage()

    def OnBankNextLongPress(self, event):
        debug.log('OnBankNext (long)', 'Dispatched', event=event)
        self.OnLivePart1(event)

    def OnBankPrev(self, event):
        self._detect_long_press(event, self.OnBankPrevShortPress, self.OnBankPrevLongPress)

    def OnBankPrevShortPress(self, event):
        debug.log('OnBankPrev (short)', 'Dispatched', event=event)
        self._controller.encoders().NextSlidersPage()

    def OnBankPrevLongPress(self, event):
        debug.log('OnBankPrev (long)', 'Dispatched', event=event)
        self.OnLivePart2(event)

    def OnLivePart1(self, event):
        debug.log('OnLivePart1', 'Dispatched', event=event)
        self._controller.encoders().SetCurrentMode(ArturiaInputControls.INPUT_MODE_CHANNEL_PLUGINS)

    def OnLivePart2(self, event):
        debug.log('OnLivePart2', 'Dispatched', event=event)
        self._controller.encoders().SetCurrentMode(ArturiaInputControls.INPUT_MODE_MIXER_OVERVIEW)

    def OnBankSelect(self, event):
        bank_index = event.controlNum - 24
        if bank_index < channels.channelCount():
            channels.selectOneChannel(bank_index)
        debug.log('OnBankSelect', 'Selected bank index=%d' % bank_index, event=event)

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
