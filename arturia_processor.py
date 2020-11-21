import arrangement
import channels
import debug
import general
import midi
import mixer
import patterns
import playlist
import transport
import ui
import utils

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
            .SetHandler(93, self.OnTransportsStop, ignore_release)
            .SetHandler(94, self.OnTransportsPausePlay, ignore_release)
            .SetHandler(95, self.OnTransportsRecord, ignore_release)
            .SetHandler(86, self.OnTransportsLoop, ignore_release)

            .SetHandler(80, self.OnGlobalSave, ignore_release)
            .SetHandler(87, self.OnGlobalIn, ignore_release)
            .SetHandler(88, self.OnGlobalOut, ignore_release)
            .SetHandler(89, self.OnGlobalMetro, ignore_release)
            .SetHandler(81, self.OnGlobalUndo, ignore_release)

            .SetHandlerForKeys(range(8, 16), self.OnTrackSolo, ignore_release)
            .SetHandlerForKeys(range(16, 24), self.OnTrackMute, ignore_release)
            .SetHandlerForKeys(range(0, 8), self.OnTrackRecord, ignore_release)

            .SetHandler(74, self.OnTrackRead, ignore_release)
            .SetHandler(75, self.OnTrackWrite, ignore_release)

            .SetHandler(98, self.OnNavigationLeft, ignore_release)
            .SetHandler(99, self.OnNavigationRight, ignore_release)
            .SetHandler(84, self.OnNavigationKnobPressed, ignore_release)

            .SetHandler(49, self.OnBankNext, ignore_release)
            .SetHandler(48, self.OnBankPrev, ignore_release)
            .SetHandler(47, self.OnLivePart1, ignore_release)
            .SetHandler(46, self.OnLivePart2, ignore_release)

            .SetHandlerForKeys(range(24, 32), self.OnBankSelect, ignore_release)
            .SetHandlerForKeys(range(104, 112), self.OnSetActiveSliderTrack, ignore_release)
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
        def get_channel_line(): return '[%s]' % channels.getChannelName(channels.selectedChannel())
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

        self._navigation = (
            NavigationMode(self._controller.paged_display())
            .AddMode('Set Volume', self.OnUpdateVolume, get_volume_line)
            .AddMode('Set Panning', self.OnUpdatePanning, get_panning_line)
            .AddMode('Set Pitch', self.OnUpdatePitch, get_pitch_line)
            .AddMode('Set Time Marker', self.OnUpdateTimeMarker, get_time_position)
            .AddMode('Set Pattern', self.OnUpdatePattern, get_pattern_line)
            .AddMode('Select Channel', self.OnUpdateChannel, get_channel_line)
            .AddMode('Plugin Preset', self.OnUpdatePlugin, get_plugin_line)
            .AddMode('Set Color RED', self.OnUpdateColorRed, get_color_red_line)
            .AddMode('Set Color GREEN', self.OnUpdateColorGreen, get_color_green_line)
            .AddMode('Set Color BLUE', self.OnUpdateColorBlue, get_color_blue_line)
        )
        self._debug_value = 0

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

    def OnUpdatePlugin(self, delta):
        # Indicator to notify user that preset is in process of being set.
        self._controller.display().SetLines(line2=' ... loading ...')
        channels.focusEditor(channels.selectedChannel())
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

    def ProcessEvent(self, event):
        return self._midi_id_dispatcher.Dispatch(event)

    def OnCommandEvent(self, event):
        self._midi_command_dispatcher.Dispatch(event)

    def OnKnobEvent(self, event):
        self._knob_dispatcher.Dispatch(event)

    def _to_rec_value(self, value):
        return int((value / 127.0) * midi.FromMIDI_Max)

    def OnSliderEvent(self, event):
        slider_index = event.status - event.midiId
        slider_value = event.controlVal

        debug.log('OnSliderEvent', 'Slider %d = %d' % (slider_index, slider_value), event=event)
        event_id = midi.REC_Mixer_Vol + mixer.getTrackPluginId(slider_index + 1, 0)
        general.processRECEvent(event_id, self._to_rec_value(slider_value),
                                midi.REC_UpdateValue | midi.REC_UpdatePlugLabel | midi.REC_ShowHint )

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
        debug.log('OnTransportsStop', 'Dispatched', event=event)
        self._controller.metronome().Reset()
        transport.stop()

    def OnTransportsPausePlay(self, event):
        debug.log('OnTransportsPausePlay', 'Dispatched', event=event)
        transport.globalTransport(midi.FPT_Play, midi.FPT_Play, event.pmeFlags)

    def OnTransportsRecord(self, event):
        debug.log('OnTransportsRecord', 'Dispatched', event=event)
        transport.record()

    def OnTransportsLoop(self, event):
        debug.log('OnTransportsLoop', 'Dispatched', event=event)
        transport.globalTransport(midi.FPT_LoopRecord, midi.FPT_LoopRecord, event.pmeFlags)

    def OnGlobalSave(self, event):
        debug.log('OnGlobalSave', 'Dispatched', event=event)
        transport.setLoopMode()

    def OnGlobalIn(self, event):
        debug.log('OnGlobalIn', 'Dispatched', event=event)
        transport.globalTransport(midi.FPT_PunchIn, midi.FPT_PunchIn, event.pmeFlags)
        self._controller.lights().SetLights({ArturiaLights.ID_GLOBAL_IN: ArturiaLights.LED_ON})

    def OnGlobalOut(self, event):
        debug.log('OnGlobalOut', 'Dispatched', event=event)
        transport.globalTransport(midi.FPT_PunchOut, midi.FPT_PunchOut, event.pmeFlags)
        if arrangement.selectionStart() < 0:
            self._controller.lights().SetLights({ArturiaLights.ID_GLOBAL_IN: ArturiaLights.LED_OFF})

    def OnGlobalMetro(self, event):
        debug.log('OnGlobalMetro', 'Dispatched', event=event)
        transport.globalTransport(midi.FPT_Metronome, midi.FPT_Metronome, event.pmeFlags)

    def OnGlobalUndo(self, event):
        debug.log('OnGlobalUndo', 'Dispatched', event=event)
        transport.globalTransport(midi.FPT_Undo, midi.FPT_Undo, event.pmeFlags)

    def OnTrackSolo(self, event):
        debug.log('OnTrackSolo', 'Dispatched', event=event)
        channels.soloChannel(channels.selectedChannel())

    def OnTrackMute(self, event):
        debug.log('OnTrackMute', 'Dispatched', event=event)
        channels.muteChannel(channels.selectedChannel())

    def OnTrackRecord(self, event):
        debug.log('OnTrackRecord', 'Dispatched', event=event)
        pattern_id = patterns.patternCount() + 1
        patterns.setPatternName(pattern_id, 'Pattern %d' % pattern_id)
        patterns.jumpToPattern(pattern_id)
        patterns.selectPattern(pattern_id, 1)

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
        debug.log('OnNavigationLeft', 'Dispatched', event=event)
        self._navigation.PreviousMode()

    def OnNavigationRight(self, event):
        debug.log('OnNavigationRight', 'Dispatched', event=event)
        self._navigation.NextMode()

    def OnNavigationKnobPressed(self, event):
        debug.log('OnNavigationKnobPressed', 'Dispatched', event=event)
        ## DEBUG ONLY ##
        transport.globalTransport(midi.FPT_F8, midi.FPT_F8)
        debug.log('DEBUG', 'Trying to show editor for %d' % channels.channelCount())

    def OnBankNext(self, event):
        debug.log('OnBankNext', 'Dispatched', event=event)
        self._controller.encoders().NextKnobsPage()

    def OnBankPrev(self, event):
        debug.log('OnBankPrev', 'Dispatched', event=event)
        self._controller.encoders().NextSlidersPage()

    def OnLivePart1(self, event): debug.log('OnLivePart1', 'Dispatched', event=event)
    def OnLivePart2(self, event): debug.log('OnLivePart2', 'Dispatched', event=event)

    def OnBankSelect(self, event):
        bank_index = event.controlNum - 24
        if bank_index < channels.channelCount():
            channels.selectOneChannel(bank_index)
        debug.log('OnBankSelect', 'Selected bank index=%d' % bank_index, event=event)

    def OnSetActiveSliderTrack(self, event): debug.log('OnSetActiveSliderTrack', 'Dispatched', event=event)