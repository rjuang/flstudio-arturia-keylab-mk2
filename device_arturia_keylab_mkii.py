# name=Arturia Keylab mkII
import channels
import device
import general
import midi
import mixer
import ui
import time
import transport


# Enable to print debugging log
_DEBUG = True

# Enable to iterate through all LEDs and toggle lights ON and OFF.
_DEBUG_LEDS = False

MIDI_ON = 127
MIDI_OFF = 0

def _log(tag, message, event=None):
    """Log out message if global _DEBUG variable is True."""
    if _DEBUG:
        event_str = _event_as_string(event) if event is not None else ''
        print('%s | [%s] %s' % (event_str, tag, message))


def _event_as_string(event):
    return '[id, status, cnum, cval, d1, d2] = %3d, %3d, %3d, %3d, %3d, %3d' % (
        event.midiId, event.status, event.controlNum, event.controlVal, event.data1, event.data2)


class MidiEventDispatcher:
    """ Dispatches a MIDI event after feeding it through a transform function.

    MIDI event dispatcher transforms the MIDI event into a value through a transform function provided at construction
    time. This value is then used as a key into a lookup table that provides a dispatcher and filter function. If the
    filter function returns true, then the event is sent to the dispatcher function.
    """
    def __init__(self, transform_fn):
        self._transform_fn = transform_fn
        # Table contains a mapping of status code -> (callback_fn, filter_fn)
        self._dispatch_map = {}

    def SetHandler(self, key, callback_fn, filter_fn=None):
        """ Associate a handler function and optional filter predicate function to a key.

        If the transform of the midi event matches the key, then the event is dispatched to the callback function
        given that the filter predicate function also returns true.

        :param key: the result value of transform_fn(event) to match against.
        :param callback_fn: function that is called with the event in the event the transformed event matches.
        :param filter_fn: function that takes an event and returns true if the event should be dispatched. If false
        is returned, then the event is dropped and never passed to callback_fn. Not specifying means that callback_fn
        is always called if transform_fn matches the key.
        """
        def _default_true_fn(_): return True
        if filter_fn is None:
            filter_fn = _default_true_fn
        self._dispatch_map[key] = (callback_fn, filter_fn)
        return self

    def SetHandlerForKeys(self, keys, callback_fn, filter_fn=None):
        """ Associate the same handler for a group of keys. See SetHandler for more details. """
        for k in keys:
            self.SetHandler(k, callback_fn, filter_fn=filter_fn)
        return self

    def Dispatch(self, event):
        """ Dispatches a midi event to the appropriate listener.

        :param event:  the event to dispatch.
        """
        key = self._transform_fn(event)
        processed = False
        if key in self._dispatch_map:
            callback_fn, filter_fn = self._dispatch_map[key]
            if filter_fn(event):
                callback_fn(event)
                processed = True
            else:
                _log("DISPATCHER", "Event dropped by filter.", event=event)
                processed = True
        else:
            _log("DISPATCHER", "No handler found.", event=event)

        return processed


def _send_to_device(data):
    """Sends a data payload to Arturia device. """
    _log('CMD', 'Sending payload: ' + str(data))
    # Reference regarding SysEx code : # https://forum.arturia.com/index.php?topic=90496.0
    device.midiOutSysex(bytes([0xF0, 0x00, 0x20, 0x6B, 0x7F, 0x42]) + data + bytes([0xF7]))


class ArturiaLights:
    """Maintains setting all the button lights, including any possible fancy animation."""

    # IDs for all of the buttons with lights.
    ID_OCTAVE_MINUS = 16
    ID_OCTAVE_PLUS = 17
    ID_CHORD = 18
    ID_TRANSPOSE = 19
    ID_MIDI_CHANNEL = 20
    ID_PAD_MODE_CHORD_TRANSPOSE = 21
    ID_PAD_MODE_CHORD_MEMORY = 22
    ID_PAD_MODE_PAD = 23
    ID_NAVIGATION_CATEGORY = 24
    ID_NAVIGATION_PRESET = 25
    ID_NAVIGATION_LEFT = 26
    ID_NAVIGATION_RIGHT = 27
    ID_NAVIGATION_ANALOG_LAB = 28
    ID_NAVIGATION_DAW = 29
    ID_NAVIGATION_USER = 30
    ID_BANK_NEXT = 31
    ID_BANK_PREVIOUS = 32
    ID_BANK_TOGGLE = 33

    # Program bank buttons (these are the channel select buttons)
    ID_BANK_SELECT1 = 34
    ID_BANK_SELECT2 = 35
    ID_BANK_SELECT3 = 36
    ID_BANK_SELECT4 = 37
    ID_BANK_SELECT5 = 38
    ID_BANK_SELECT6 = 39
    ID_BANK_SELECT7 = 40
    ID_BANK_SELECT8 = 41
    ID_BANK_SELECT9 = 42    # This is also the master/multi button

    # Array representation for the bank lights
    ARRAY_IDS_BANK_SELECT = [
        ID_BANK_SELECT1, ID_BANK_SELECT2, ID_BANK_SELECT3, ID_BANK_SELECT4, ID_BANK_SELECT5, ID_BANK_SELECT6,
        ID_BANK_SELECT7, ID_BANK_SELECT8, ID_BANK_SELECT9]

    # Track controls
    ID_TRACK_SOLO = 96
    ID_TRACK_MUTE = 97
    ID_TRACK_RECORD = 98
    ID_TRACK_READ = 99
    ID_TRACK_WRITE = 100

    # Global controls
    ID_GLOBAL_SAVE = 101
    ID_GLOBAL_IN = 102
    ID_GLOBAL_OUT = 103
    ID_GLOBAL_METRO = 104
    ID_GLOBAL_UNDO = 105

    # Transports section
    ID_TRANSPORTS_REWIND = 106
    ID_TRANSPORTS_FORWARD = 107
    ID_TRANSPORTS_STOP = 108
    ID_TRANSPORTS_PLAY = 109
    ID_TRANSPORTS_RECORD = 110
    ID_TRANSPORTS_LOOP = 111

    # 4x4 pad
    ID_PAD_R1_C1 = 112
    ID_PAD_R1_C2 = 113
    ID_PAD_R1_C3 = 114
    ID_PAD_R1_C4 = 115

    ID_PAD_R2_C1 = 116
    ID_PAD_R2_C2 = 117
    ID_PAD_R2_C3 = 118
    ID_PAD_R2_C4 = 119

    ID_PAD_R3_C1 = 120
    ID_PAD_R3_C2 = 121
    ID_PAD_R3_C3 = 122
    ID_PAD_R3_C4 = 123

    ID_PAD_R4_C1 = 124
    ID_PAD_R4_C2 = 125
    ID_PAD_R4_C3 = 126
    ID_PAD_R4_C4 = 127

    # 4x4 lookup for the pad ids.
    MATRIX_IDS_PAD = [
        [ID_PAD_R1_C1, ID_PAD_R1_C2, ID_PAD_R1_C3, ID_PAD_R1_C4],
        [ID_PAD_R2_C1, ID_PAD_R2_C2, ID_PAD_R2_C3, ID_PAD_R2_C4],
        [ID_PAD_R3_C1, ID_PAD_R3_C2, ID_PAD_R3_C3, ID_PAD_R3_C4],
        [ID_PAD_R4_C1, ID_PAD_R4_C2, ID_PAD_R4_C3, ID_PAD_R4_C4],
    ]

    SET_COLOR_COMMAND = bytes([0x02, 0x00, 0x10])

    def __init__(self):
        pass

    def SetPadLights(self, matrix_values):
        """ Set the pad lights given a matrix of color values to set the pad with.
        :param matrix_values: 4x4 array of arrays containing the LED color values.
        """
        # Note: Pad lights can be set to RGB colors, but this doesn't seem to be working.
        led_map = {}
        for r in range(4):
            for c in range(4):
                led_map[ArturiaLights.MATRIX_IDS_PAD[r][c]] = matrix_values[r][c]
        self.SetLights(led_map)

    def SetBankLights(self, array_values):
        """ Set the bank lights given an array of color values to set the bank lights with.

        :param array_values: a 9-element array containing the LED color values.
        """
        led_map = {k : v for k, v in zip(ArturiaLights.ARRAY_IDS_BANK_SELECT, array_values)}
        self.SetLights(led_map)

    def SetLights(self, led_mapping):
        """ Given a map of LED ids to color value, construct and send a command with all the led mapping. """
        data = bytes([])
        for led_id, led_value in led_mapping.items():
            data += bytes([led_id, led_value])
        _send_to_device(ArturiaLights.SET_COLOR_COMMAND + data)


class ArturiaDisplay:
    """ Manages scrolling display of two lines so that long strings can be scrolled on each line. """
    def __init__(self):
        # Holds the text to display on first line. May exceed the 16-char display limit.
        self._line1 = ' '
        # Holds the text to display on second line. May exceed the 16-char display limit.
        self._line2 = ' '
        # Holds the starting offset of where the line1 text should start.
        self._line1_display_offset = 0
        # Holds the starting offset of where the line2 text should start.
        self._line2_display_offset = 0
        # Last timestamp in milliseconds in which the text was updated.
        self._last_update_ms = 0
        # Minimum refresh interval before text is updated (for scrolling).
        self._refresh_interval_ms = 500
        # How many characters to allow last char to scroll before starting over.
        self._end_padding = 8
        # Track what's currently being displayed
        self._last_payload = bytes()

    def _get_line1_bytes(self):
        # Get up to 16-bytes the exact chars to display for line 1. Also increment the scroll position by 1.
        start_pos = self._line1_display_offset
        end_pos = start_pos + 16
        if end_pos >= len(self._line1) + self._end_padding or len(self._line1) <= 16:
            self._line1_display_offset = 0
        else:
            self._line1_display_offset += 1
        return bytearray(self._line1[start_pos:end_pos], 'ascii')

    def _get_line2_bytes(self):
        # Get up to 16-bytes the exact chars to display for line 2. Also increment the scroll position by 1.
        start_pos = self._line2_display_offset
        end_pos = start_pos + 16
        if end_pos >= len(self._line2) + self._end_padding or len(self._line2) <= 16:
            self._line2_display_offset = 0
        else:
            self._line2_display_offset += 1
        return bytearray(self._line2[start_pos:end_pos], 'ascii')

    @staticmethod
    def _get_time_ms():
        # Get the current timestamp in milliseconds
        return time.monotonic() * 1000

    def _refresh_display(self):
        # Internally called to refresh the display now.
        data = bytes([0x04, 0x00, 0x60])
        data += bytes([0x01]) + self._get_line1_bytes() + bytes([0x00])
        data += bytes([0x02]) + self._get_line2_bytes() + bytes([0x00])
        data += bytes([0x7F])
        self._last_update_ms = self._get_time_ms()
        if self._last_payload != data:
            _send_to_device(data)
            self._last_payload = data

    def SetRefreshInterval(self, min_interval_ms):
        """ Sets the minimum time elapsed before next refresh. """
        self._refresh_interval_ms = min_interval_ms

    def SetLines(self, line1=None, line2=None):
        """ Update lines on the display, or leave alone if not provided.

        :param line1:  first line to update display with or None to leave as is.
        :param line2:  second line to update display with or None to leave as is.
        """
        if line1 is not None:
            self._line1 = line1
            self._line1_display_offset = 0
        if line2 is not None:
            self._line2 = line2
            self._line2_display_offset = 0
        self._refresh_display()
        return self

    def Refresh(self):
        """ Called to refresh the display, possibly with updated text. """
        if self._get_time_ms() - self._last_update_ms >= self._refresh_interval_ms:
            self._refresh_display()
        return self


class ArturiaController:
    def __init__(self):
        self._display = ArturiaDisplay()
        self._lights = ArturiaLights()

    def display(self):
        return self._display

    def lights(self):
        return self._lights

    def _onoff_byte(self, is_on):
        return MIDI_ON if is_on else MIDI_OFF

    def Sync(self):
        """ Syncs up all visual indicators on keyboard with changes from FL Studio. """
        # Update buttons
        active_index = channels.selectedChannel()
        led_map = {
            ArturiaLights.ID_TRANSPORTS_RECORD: self._onoff_byte(transport.isRecording()),
            ArturiaLights.ID_TRANSPORTS_LOOP: self._onoff_byte(ui.isLoopRecEnabled()),
            ArturiaLights.ID_GLOBAL_METRO: self._onoff_byte(ui.isMetronomeEnabled()),
            ArturiaLights.ID_GLOBAL_SAVE: self._onoff_byte(transport.getLoopMode() == 1),
            ArturiaLights.ID_GLOBAL_UNDO: self._onoff_byte(general.getUndoHistoryLast() == 0),
            ArturiaLights.ID_TRACK_SOLO: self._onoff_byte(channels.isChannelSolo(active_index)),
            ArturiaLights.ID_TRACK_MUTE: self._onoff_byte(channels.isChannelMuted(active_index)),
        }
        self._lights.SetLights(led_map)

        # Update selected channel
        bank_lights = [MIDI_OFF] * 9
        if active_index < len(bank_lights):
            bank_lights[active_index] = MIDI_ON
        self._lights.SetBankLights(bank_lights)

        # Update display
        name = channels.getChannelName(active_index)
        volume = int(channels.getChannelVolume(active_index) * 100)
        pan = int(channels.getChannelPan(active_index) * 100)
        self._display.SetLines(line1='Ch%d: %s' % (active_index + 1, name), line2='Vol:%d Pan:%d' % (volume, pan))


class ArturiaMidiProcessor:
    def __init__(self, controller):
        def by_midi_id(event): return event.midiId
        def by_control_num(event): return event.controlNum
        def ignore_release(event): return event.controlVal != 0

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

        self._debug_value = 0

    def ProcessEvent(self, event):
        return self._midi_id_dispatcher.Dispatch(event)

    def OnCommandEvent(self, event):
        self._midi_command_dispatcher.Dispatch(event)

    def OnKnobEvent(self, event):
        self._knob_dispatcher.Dispatch(event)

    def OnSliderEvent(self, event):
        slider_index = event.status - event.midiId
        slider_value = event.controlVal
        _log('OnSliderEvent', 'Slider %d = %d' % (slider_index, slider_value), event=event)

    @staticmethod
    def _get_knob_delta(event):
        val = event.controlVal
        return val if val < 64 else 64 - val

    def OnNavigationKnobTurned(self, event):
        delta = self._get_knob_delta(event)
        if _DEBUG_LEDS:
            self._debug_value = max(0, min(255, self._debug_value + delta))
            self._controller.lights().SetLights({ArturiaLights.ID_PAD_R1_C1 : self._debug_value})
            self._controller.display().SetLines(line2='LED value=%d' % self._debug_value)
            _log('LED', 'Value=%d' % self._debug_value, event=event)

        _log('OnNavigationKnob', 'Delta = %d' % delta, event=event)

    def OnPanKnobTurned(self, event):
        idx = event.controlNum - 16
        delta = self._get_knob_delta(event)
        _log('OnPanKnobTurned', 'Knob %d Delta = %d' % (idx, delta), event=event)

    def OnTransportsBack(self, event): _log('OnTransportsBack', 'Dispatched', event=event)
    def OnTransportsForward(self, event): _log('OnTransportsForward', 'Dispatched', event=event)

    def OnTransportsStop(self, event):
        _log('OnTransportsStop', 'Dispatched', event=event)
        transport.stop()

    def OnTransportsPausePlay(self, event): _log('OnTransportsPausePlay', 'Dispatched', event=event)
    def OnTransportsRecord(self, event): _log('OnTransportsRecord', 'Dispatched', event=event)
    def OnTransportsLoop(self, event): _log('OnTransportsLoop', 'Dispatched', event=event)

    def OnGlobalSave(self, event):
        _log('OnGlobalSave', 'Dispatched', event=event)
        transport.setLoopMode()

    def OnGlobalIn(self, event):
        _log('OnGlobalIn', 'Dispatched', event=event)
        transport.globalTransport(midi.FPT_PunchIn, 31)

    def OnGlobalOut(self, event):
        _log('OnGlobalOut', 'Dispatched', event=event)
        transport.globalTransport(midi.FPT_PunchOut, 32)

    def OnGlobalMetro(self, event):
        _log('OnGlobalMetro', 'Dispatched', event=event)
        transport.globalTransport(midi.FPT_Metronome, 110)

    def OnGlobalUndo(self, event):
        _log('OnGlobalUndo', 'Dispatched', event=event)
        transport.globalTransport(midi.FPT_Undo, 20)

    def OnTrackSolo(self, event):
        _log('OnTrackSolo', 'Dispatched', event=event)
        channels.soloChannel(channels.selectedChannel())

    def OnTrackMute(self, event):
        _log('OnTrackMute', 'Dispatched', event=event)
        channels.muteChannel(channels.selectedChannel())

    def OnTrackRecord(self, event): _log('OnTrackRecord', 'Dispatched', event=event)
    def OnTrackRead(self, event): _log('OnTrackRead', 'Dispatched', event=event)
    def OnTrackWrite(self, event): _log('OnTrackWrite', 'Dispatched', event=event)

    def OnNavigationLeft(self, event): _log('OnNavigationLeft', 'Dispatched', event=event)
    def OnNavigationRight(self, event): _log('OnNavigationRight', 'Dispatched', event=event)
    def OnNavigationKnobPressed(self, event): _log('OnNavigationKnobPressed', 'Dispatched', event=event)

    def OnBankNext(self, event): _log('OnBankNext', 'Dispatched', event=event)
    def OnBankPrev(self, event): _log('OnBankPrev', 'Dispatched', event=event)

    def OnLivePart1(self, event): _log('OnLivePart1', 'Dispatched', event=event)
    def OnLivePart2(self, event): _log('OnLivePart2', 'Dispatched', event=event)

    def OnBankSelect(self, event):
        bank_index = event.controlNum - 24
        if bank_index < channels.channelCount():
            channels.selectOneChannel(bank_index)
        _log('OnBankSelect', 'Selected bank index=%d' % bank_index, event=event)


    def OnSetActiveSliderTrack(self, event): _log('OnSetActiveSliderTrack', 'Dispatched', event=event)


# --------------------[ Global state for MIDI Script ] ------------------------------------------

_controller = ArturiaController()
_processor = ArturiaMidiProcessor(_controller)


# --------------------[ MIDI Script Integration Events for FL Studio ]---------------------------

def OnInit():
    global _controller
    print('Loaded MIDI script for Arturia Keylab mkII')
    _controller.Sync()


def OnIdle():
    _controller.display().Refresh()


def OnMidiMsg(event):
    if _processor.ProcessEvent(event):
        event.handled = True


def OnProgramChange(event):
    print('OnProgramChange')


def OnRefresh(event):
    print('OnRefresh')
    _controller.Sync()
    #_sync_state_from_daw()


def OnUpdateBeatIndicator(event):
    print('OnUpdateBeatIndicator')
