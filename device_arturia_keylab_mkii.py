# name=Arturia Keylab mkII
import channels
import device
import general
import midi
import mixer
import playlist
import ui
import transport

# Enable to print debugging log
_DEBUG = True

# Enable to iterate through all LEDs and toggle lights ON and OFF.
_DEBUG_LEDS = False

MIDI_ON = 127
MIDI_OFF = 0

# Maps eventData.status values to a handler function that takes an input eventData argument.
STATUS_HANDLER_MAP = {
    144: lambda e: _handle_command_event(e),
    176: lambda e: _handle_knob_event(e),
    # Slider events have a different status code per channel.
    224: lambda e: _handle_slider_event(e, 1),
    225: lambda e: _handle_slider_event(e, 2),
    226: lambda e: _handle_slider_event(e, 3),
    227: lambda e: _handle_slider_event(e, 4),
    228: lambda e: _handle_slider_event(e, 5),
    229: lambda e: _handle_slider_event(e, 6),
    230: lambda e: _handle_slider_event(e, 7),
    231: lambda e: _handle_slider_event(e, 8),
    232: lambda e: _handle_slider_event(e, 9),
}

COMMAND_HANDLER_MAP = {
    # Handler for buttons in the TRANSPORTS section of keyboard
    91: lambda e: _on_transports_back(e),
    92: lambda e: _on_transports_forward(e),
    93: lambda e: _on_transports_stop(e),
    94: lambda e: _on_transports_pause_play(e),
    95: lambda e: _on_transports_record(e),
    86: lambda e: _on_transports_loop(e),

    # Handler for buttons under the GLOBAL CONTROLS section of keyboard
    80: lambda e: _on_global_save(e),
    87: lambda e: _on_global_in(e),
    88: lambda e: _on_global_out(e),
    89: lambda e: _on_global_metro(e),
    81: lambda e: _on_global_undo(e),

    # Buttons under the TRACK CONTROLS section of keyboard
    # These buttons will emit different codes depending on what track is selected.
    # Solo button for each track
    8: lambda e: _on_track_solo(e, 1),
    9: lambda e: _on_track_solo(e, 2),
    10: lambda e: _on_track_solo(e, 3),
    11: lambda e: _on_track_solo(e, 4),
    12: lambda e: _on_track_solo(e, 5),
    13: lambda e: _on_track_solo(e, 6),
    14: lambda e: _on_track_solo(e, 7),
    15: lambda e: _on_track_solo(e, 8),

    # Mute button for each track
    16: lambda e: _on_track_mute(e, 1),
    17: lambda e: _on_track_mute(e, 2),
    18: lambda e: _on_track_mute(e, 3),
    19: lambda e: _on_track_mute(e, 4),
    20: lambda e: _on_track_mute(e, 5),
    21: lambda e: _on_track_mute(e, 6),
    22: lambda e: _on_track_mute(e, 7),
    23: lambda e: _on_track_mute(e, 8),

    # Record button for each track
    0: lambda e: _on_track_record(e, 1),
    1: lambda e: _on_track_record(e, 2),
    2: lambda e: _on_track_record(e, 3),
    3: lambda e: _on_track_record(e, 4),
    4: lambda e: _on_track_record(e, 5),
    5: lambda e: _on_track_record(e, 6),
    6: lambda e: _on_track_record(e, 7),
    7: lambda e: _on_track_record(e, 8),

    # Remaining track buttons (same code regardless of track selected)
    74: lambda e: _on_track_read(e),  # Corresponds to ARM for Ableton Live template.
    75: lambda e: _on_track_write(e),  # Corresponds to Re-Enable for Ableton Live template.

    # Buttons under the TOUCH SCREEN section of keyboard
    98: lambda e: _on_navigation_left(e),
    99: lambda e: _on_navigation_right(e),
    84: lambda e: _on_navigation_knob_press(e),

    # Buttons to the left of sliders
    # When the "Live" button LED is OFF:
    49: lambda e: _on_bank_next(e),
    48: lambda e: _on_bank_previous(e),

    # When the "Live" button LED is ON:
    47: lambda e: _on_live_part1(e),
    46: lambda e: _on_live_part2(e),

    # Program bank Buttons under sliders
    24: lambda e: _on_bank_select(e, 1),
    25: lambda e: _on_bank_select(e, 2),
    26: lambda e: _on_bank_select(e, 3),
    27: lambda e: _on_bank_select(e, 4),
    28: lambda e: _on_bank_select(e, 5),
    29: lambda e: _on_bank_select(e, 6),
    30: lambda e: _on_bank_select(e, 7),
    31: lambda e: _on_bank_select(e, 8),

    104: lambda e: _on_set_active_track(e, 1),
    105: lambda e: _on_set_active_track(e, 2),
    106: lambda e: _on_set_active_track(e, 3),
    107: lambda e: _on_set_active_track(e, 4),
    108: lambda e: _on_set_active_track(e, 5),
    109: lambda e: _on_set_active_track(e, 6),
    110: lambda e: _on_set_active_track(e, 7),
    111: lambda e: _on_set_active_track(e, 8),
}

KNOB_HANDLER_MAP = {
    16: lambda e, delta: _on_knob_pan(e, delta, 1),
    17: lambda e, delta: _on_knob_pan(e, delta, 2),
    18: lambda e, delta: _on_knob_pan(e, delta, 3),
    19: lambda e, delta: _on_knob_pan(e, delta, 4),
    20: lambda e, delta: _on_knob_pan(e, delta, 5),
    21: lambda e, delta: _on_knob_pan(e, delta, 6),
    22: lambda e, delta: _on_knob_pan(e, delta, 7),
    23: lambda e, delta: _on_knob_pan(e, delta, 8),
    24: lambda e, delta: _on_knob_pan(e, delta, 9),
    60: lambda e, delta: _on_knob_navigation(e, delta),
}

LED_ID_MAP = {
    'octave-': 16,
    'octave+': 17,
    'chord': 18,
    'transpose': 19,
    'midi channel': 20,
    'chord transpose': 21,
    'chord memory': 22,
    'pad': 23,
    'category': 24,
    'preset': 25,
    'navigate left': 26,
    'navigate right': 27,
    'analog lab': 28,
    'daw': 29,
    'user': 30,
    'bank next': 31,
    'bank previous': 32,
    'bank': 33,

    # Program bank
    'select1': 34,
    'select2': 35,
    'select3': 36,
    'select4': 37,
    'select5': 38,
    'select6': 39,
    'select7': 40,
    'select8': 41,
    'select0': 42,  # This is the master/multi button

    # Track controls
    'solo': 96,
    'multi': 97,
    'arm record': 98,
    'read': 99,
    'write': 100,

    # Global controls
    'save': 101,
    'in': 102,
    'out': 103,
    'metro': 104,
    'undo': 105,

    # Transports section
    '<<': 106,
    '>>': 107,
    'stop': 108,
    'play': 109,
    'rec': 110,
    'loop': 111,

    # 4x4 pad
    'pad1': 112,
    'pad2': 113,
    'pad3': 114,
    'pad4': 115,
    'pad5': 116,
    'pad6': 117,
    'pad7': 118,
    'pad8': 119,
    'pad9': 120,
    'pad10': 121,
    'pad11': 122,
    'pad12': 123,
    'pad13': 124,
    'pad14': 125,
    'pad15': 126,
    'pad16': 127,
}

# Holds the currently active track that is selected by the sliders.
_active_track = 0

# Holds the led states as tracked by the script
_led_state = {}

# Holds the last display lines
_display_line1 = ''
_display_line2 = ''

# Holds the current led (DEBUGGING ONLY)
_debug_current_led_id = 0


def _get_led_state(led_id):
    return _led_state[led_id] if led_id in _led_state else False


def _log(tag, message, event=None):
    if _DEBUG:
        event_str = _event_as_string(event) if event is not None else ''
        print('[%s] %s %s' % (tag, message, event_str))


def _send_to_device(data):
    print('Sending payload: ' + str(data))
    # Reference regarding SysEx code : # https://forum.arturia.com/index.php?topic=90496.0
    device.midiOutSysex(bytes([0xF0, 0x00, 0x20, 0x6B, 0x7F, 0x42]) + data + bytes([0xF7]))


def _set_lights(led_id, is_on):
    _led_state[led_id] = is_on
    _send_to_device(bytes([0x02, 0x00, 0x10, 0x00, 0x00, led_id, MIDI_ON if is_on else MIDI_OFF]))


def _encode_display_line(line):
    # Text needs to be up to 16 characters but doesn't need to be exactly 16 chars. Missing values are cleared.
    return bytearray(line[:16], 'ascii')


def _set_display(line1=None, line2=None):
    """ Update the Display panel on the keyboard.

    The display consists of two 16-char lines. The user can specify a specific line to update. If no line is provided,
    then the previously displayed line (set by this method) will be preserved. If the line exceeds 16 chars, then the
    line is truncated to display the first 16-chars. TODO: Support scrolling text.

    :param line1:  first line to display or None to preserve the text on first line.
    :param line2:  second line to display or None to preserve the text on first line.
    """
    global _display_line1
    global _display_line2

    # In the event only one line is requested to be updated, then we just use the previously set text for the
    # missing line. User must explicitly pass an empty string to clear the line.

    if line1 is None:
        line1 = _display_line1
    if line2 is None:
        line2 = _display_line2

    # Arturia does not refresh the display until two lines are received.
    data = bytes([0x04, 0x00, 0x60])
    data += bytes([0x01]) + _encode_display_line(line1) + bytes([0x00])
    data += bytes([0x02]) + _encode_display_line(line2) + bytes([0x00])
    data += bytes([0x7F])

    _display_line1 = line1
    _display_line2 = line2
    _send_to_device(data)


# Handles processing a midi command event (usually corresponding to a button press)
def _handle_command_event(event):
    if event.data1 in COMMAND_HANDLER_MAP:
        if event.data2 != MIDI_OFF:
            COMMAND_HANDLER_MAP[event.data1](event)
    else:
        _log('ERROR', 'Unhandled command %d' % event.data1, event)


# Handles processing a midi event corresponding to a slider event.
def _handle_slider_event(event, channel):
    value = event.data2
    _log('SLIDER%d : %d' % (channel, value), 'Event dispatched.', event)


def _get_knob_delta(event):
    value = event.data2
    return value if value < 64 else 64 - value


def _is_channel_mode():
    return transport.getLoopMode() == 0

# Handles processing a midi event corresponding to a knob event.
def _handle_knob_event(event):
    if event.data1 in KNOB_HANDLER_MAP:
        KNOB_HANDLER_MAP[event.data1](event, _get_knob_delta(event))
    else:
        _log('ERROR', "Unhandled knob %d" % event.data1, event)


def _set_selected_track(track_id):
    for i in range(9):
        button_id = 'select%d' % i
        _set_lights(LED_ID_MAP[button_id], i == track_id)


def _sync_state_from_daw():
    _set_lights(LED_ID_MAP['rec'], transport.isRecording())
    _set_lights(LED_ID_MAP['loop'], ui.isLoopRecEnabled())
    _set_lights(LED_ID_MAP['metro'], ui.isMetronomeEnabled())
    _set_lights(LED_ID_MAP['save'], transport.getLoopMode() == 1)
    _set_lights(LED_ID_MAP['undo'], general.getUndoHistoryLast() == 0)
    if _is_channel_mode():
        _set_selected_track(channels.selectedChannel() + 1)
    else:
        _set_selected_track(mixer.trackNumber())


def _on_transports_back(event):
    _log('TransportsBack', 'Event dispatched', event)
    # TODO: need to be able to process release event here
    transport.globalTransport(midi.FPT_Left, 42)


def _on_transports_forward(event):
    _log('TransportsForward', 'Event dispatched', event)
    # TODO: need to be able to process release event here
    transport.globalTransport(midi.FPT_Right, 43)


def _on_transports_stop(event):
    _log('TransportsStop', 'Event dispatched', event)
    transport.stop()


def _on_transports_pause_play(event):
    _log('TransportsPausePlay', 'Event dispatched', event)


def _on_transports_record(event):
    _log('TransportsRecord', 'Event dispatched', event)


def _on_transports_loop(event):
    _log('TransportsLoop', 'Event dispatched', event)


def _on_global_save(event):
    _log('GlobalSave', 'Event dispatched', event)
    # Toggle pattern/song mode.
    transport.setLoopMode()


def _on_global_in(event):
    _log('GlobalIn', 'Event dispatched', event)
    transport.globalTransport(midi.FPT_PunchIn, 31)


def _on_global_out(event):
    _log('GlobalOut', 'Event dispatched', event)
    transport.globalTransport(midi.FPT_PunchOut, 32)


def _on_global_metro(event):
    _log('GlobalMetro', 'Event dispatched', event)
    transport.globalTransport(midi.FPT_Metronome, 110)


def _on_global_undo(event):
    _log('GlobalUndo', 'Event dispatched', event)
    transport.globalTransport(midi.FPT_Undo, 20)


def _on_track_solo(event, track):
    _log('TrackSolo%d' % track, 'Event dispatched', event)

    # The specific channel might be out of sync with FL Studio. So need to dynamically fetch the active channel/track
    if _is_channel_mode():
        track = channels.selectedChannel()
        channels.soloChannel(track)
    else:
        track = mixer.trackNumber()
        mixer.soloTrack(track)



def _on_track_mute(event, track):
    _log('TrackMute%d' % track, 'Event dispatched', event)

    # The specific channel might be out of sync with FL Studio. So need to dynamically fetch the active channel/track
    if _is_channel_mode():
        track = channels.selectedChannel()
        channels.muteChannel(track)
    else:
        track = mixer.trackNumber()
        mixer.muteTrack(track)



def _on_track_record(event, track):
    _log('TrackRecord%d' % track, 'Event dispatched', event)


def _on_track_read(event):
    _log('TrackRead', 'Event dispatched', event)


def _on_track_write(event):
    _log('TrackWrite', 'Event dispatched', event)


def _on_navigation_left(event):
    _log('NavigationLeft', 'Event dispatched', event)


def _on_navigation_right(event):
    _log('NavigationRight', 'Event dispatched', event)


def _update_debug_led(led_state):
    global _debug_current_led_id
    _set_lights(_debug_current_led_id, led_state)
    _set_display(line1='LED %d: [%s]' % (_debug_current_led_id, 'ON' if led_state else 'OFF'))


def _on_navigation_knob_press(event):
    global _debug_current_led_id
    _log('NavigationKnobPressed', 'Event dispatched', event)
    if _DEBUG_LEDS:
        led_state = not _get_led_state(_debug_current_led_id)
        _update_debug_led(led_state)


def _on_bank_next(event):
    _log('BankNext', 'Event dispatched', event)


def _on_bank_previous(event):
    _log('BankPrevious', 'Event dispatched', event)


def _on_live_part1(event):
    _log('LivePart1', 'Event dispatched', event)


def _on_live_part2(event):
    _log('LivePart2', 'Event dispatched', event)


def _on_bank_select(event, track):
    _log('BankSelect%d' % track, 'Event dispatched', event)


def _on_set_active_track(event, track):
    global _active_track
    # Ignore the off message
    if event.data2 == MIDI_ON:
        _active_track = track
        _log('SetActiveTrack', 'Active track set to %d' % track, event)


def _on_knob_pan(event, delta, index):
    _log('OnKnobPan%d : %d' % (index, delta), 'Event dispatched', event)


def _on_knob_navigation(event, delta):
    global _debug_current_led_id
    _log('OnKnobNavigation : %d' % delta, 'Event dispatched', event)

    if _DEBUG_LEDS:
        _set_lights(_debug_current_led_id, False)
        _debug_current_led_id = max(0, min(255, _debug_current_led_id + delta))
        _update_debug_led(True)


def _event_as_string(eventData):
    values = [
        eventData.status,
        eventData.data1,
        eventData.data2,
        eventData.port,
        eventData.note,
        eventData.velocity,
        eventData.pressure,
        eventData.progNum,
        eventData.controlNum,
        eventData.controlVal,
        eventData.pitchBend,
        eventData.inEv,
        eventData.outEv,
        eventData.midiId,
        eventData.midiChan,
        eventData.midiChanEx
    ]
    return str(values)


def OnInit():
    print('Loaded MIDI script for Arturia Keylab mkII')
    _set_display(line1='Hello', line2='World')


def OnMidiMsg(event):
    eventStr = _event_as_string(event)
    if event.status in STATUS_HANDLER_MAP:
        STATUS_HANDLER_MAP[event.status](event)
        event.handled = True
    else:
        print('Unhandled status code: %d | %s' % (event.status, eventStr))

# NOTE:  Do not define OnSysEx. Causes crash when switching modes.


def OnProgramChange(event):
    print('OnProgramChange')


def OnRefresh(event):
    print('OnRefresh')
    _sync_state_from_daw()


def OnUpdateBeatIndicator(event):
    print('OnUpdateBeatIndicator')
