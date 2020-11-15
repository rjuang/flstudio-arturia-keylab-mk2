# name=Arturia Keylab mkII

import device

# Enable to print debugging log
_DEBUG = True

MIDI_ON = 127
MIDI_OFF = 0

# Maps eventData.status values to a handler function that takes an input eventData argument.
STATUS_HANDLER_MAP = {
    144: lambda e: _handleCommandEvent(e),
    176: lambda e: _handleKnobEvent(e),
    # Slider events have a different status code per channel.
    224: lambda e: _handleSliderEvent(e, 1),
    225: lambda e: _handleSliderEvent(e, 2),
    226: lambda e: _handleSliderEvent(e, 3),
    227: lambda e: _handleSliderEvent(e, 4),
    228: lambda e: _handleSliderEvent(e, 5),
    229: lambda e: _handleSliderEvent(e, 6),
    230: lambda e: _handleSliderEvent(e, 7),
    231: lambda e: _handleSliderEvent(e, 8),
    232: lambda e: _handleSliderEvent(e, 9),
}

COMMAND_HANDLER_MAP = {
    # Handler for buttons in the TRANSPORTS section of keyboard
    91: lambda e: _onTransportsBack(e),
    92: lambda e: _onTransportsForward(e),
    93: lambda e: _onTransportsStop(e),
    94: lambda e: _onTransportsPausePlay(e),
    95: lambda e: _onTransportsRecord(e),
    86: lambda e: _onTransportsLoop(e),

    # Handler for buttons under the GLOBAL CONTROLS section of keyboard
    80: lambda e: _onGlobalSave(e),
    87: lambda e: _onGlobalIn(e),
    88: lambda e: _onGlobalOut(e),
    89: lambda e: _onGlobalMetro(e),
    81: lambda e: _onGlobalUndo(e),

    # Buttons under the TRACK CONTROLS section of keyboard
    # These buttons will emit different codes depending on what track is selected.
    # Solo button for each track
    8: lambda e: _onTrackSolo(e, 1),
    9: lambda e: _onTrackSolo(e, 2),
    10: lambda e: _onTrackSolo(e, 3),
    11: lambda e: _onTrackSolo(e, 4),
    12: lambda e: _onTrackSolo(e, 5),
    13: lambda e: _onTrackSolo(e, 6),
    14: lambda e: _onTrackSolo(e, 7),
    15: lambda e: _onTrackSolo(e, 8),

    # Mute button for each track
    16: lambda e: _onTrackMute(e, 1),
    17: lambda e: _onTrackMute(e, 2),
    18: lambda e: _onTrackMute(e, 3),
    19: lambda e: _onTrackMute(e, 4),
    20: lambda e: _onTrackMute(e, 5),
    21: lambda e: _onTrackMute(e, 6),
    22: lambda e: _onTrackMute(e, 7),
    23: lambda e: _onTrackMute(e, 8),

    # Record button for each track
    0: lambda e: _onTrackRecord(e, 1),
    1: lambda e: _onTrackRecord(e, 2),
    2: lambda e: _onTrackRecord(e, 3),
    3: lambda e: _onTrackRecord(e, 4),
    4: lambda e: _onTrackRecord(e, 5),
    5: lambda e: _onTrackRecord(e, 6),
    6: lambda e: _onTrackRecord(e, 7),
    7: lambda e: _onTrackRecord(e, 8),

    # Remaining track buttons (same code regardless of track selected)
    74: lambda e: _onTrackRead(e),  # Corresponds to ARM for Ableton Live template.
    75: lambda e: _onTrackWrite(e),  # Corresponds to Re-Enable for Ableton Live template.

    # Buttons under the TOUCH SCREEN section of keyboard
    98: lambda e: _onNavigationLeft(e),
    99: lambda e: _onNavigationRight(e),

    # Buttons to the left of sliders
    # When the "Live" button LED is OFF:
    49: lambda e: _onBankNext(e),
    48: lambda e: _onBankPrevious(e),

    # When the "Live" button LED is ON:
    47: lambda e: _onLivePart1(e),
    46: lambda e: _onLivePart2(e),

    # Program bank Buttons under sliders
    24: lambda e: _onBankSelect(e, 1),
    25: lambda e: _onBankSelect(e, 2),
    26: lambda e: _onBankSelect(e, 3),
    27: lambda e: _onBankSelect(e, 4),
    28: lambda e: _onBankSelect(e, 5),
    29: lambda e: _onBankSelect(e, 6),
    30: lambda e: _onBankSelect(e, 7),
    31: lambda e: _onBankSelect(e, 8),

    104: lambda e: _onSetActiveTrack(e, 1),
    105: lambda e: _onSetActiveTrack(e, 2),
    106: lambda e: _onSetActiveTrack(e, 3),
    107: lambda e: _onSetActiveTrack(e, 4),
    108: lambda e: _onSetActiveTrack(e, 5),
    109: lambda e: _onSetActiveTrack(e, 6),
    110: lambda e: _onSetActiveTrack(e, 7),
    111: lambda e: _onSetActiveTrack(e, 8),
}

KNOB_HANDLER_MAP = {
    16: lambda e, delta: _onKnobPan(e, delta, 1),
    17: lambda e, delta: _onKnobPan(e, delta, 2),
    18: lambda e, delta: _onKnobPan(e, delta, 3),
    19: lambda e, delta: _onKnobPan(e, delta, 4),
    20: lambda e, delta: _onKnobPan(e, delta, 5),
    21: lambda e, delta: _onKnobPan(e, delta, 6),
    22: lambda e, delta: _onKnobPan(e, delta, 7),
    23: lambda e, delta: _onKnobPan(e, delta, 8),
    24: lambda e, delta: _onKnobPan(e, delta, 9),
    60: lambda e, delta: _onKnobNavigation(e, delta),
}

_activeTrack = 0


def _printToLogs(tag, message, event):
    global _DEBUG
    if _DEBUG:
        eventStr = _eventAsString(event)
        print('[%s] %s %s' % (tag, message, eventStr))

# From:
# https://forum.arturia.com/index.php?topic=90496.0
def _sendPayload(data):
    print('Sending payload: ' + str(data))
    device.midiOutSysex(bytes([0xF0, 0x00, 0x20, 0x6B, 0x7F, 0x42]) + data + bytes([0xF7]))


def _setLED(ledId, isOn):
    _sendPayload(bytes([0x02, 0x00, 0x10, 0x00, 0x00, ledId, MIDI_ON if isOn else MIDI_OFF]))

def _encodeDisplayLine(line):
    # Has to be 16 chars
    bytes = bytearray(line[:16], 'ascii')
    if len(bytes) < 16:
        bytes += b' ' * (16 - len(bytes))
    return bytes

def _setDisplay(line1=None, line2=None):
    data = None
    if line1 is not None or line2 is not None:
        data = bytes([0x04, 0x00, 0x60])

    if line1 is not None:
        data += bytes([0x01]) + _encodeDisplayLine(line1) + bytes([0x00])

    if line2 is not None:
        data += bytes([0x02]) + _encodeDisplayLine(line1) + bytes([0x00])

    if data is not None:
        data += bytes([0x7F])
        _sendPayload(data)


# Handles processing a midi command event (usually corresponding to a button press)
def _handleCommandEvent(event):
    if event.data1 in COMMAND_HANDLER_MAP:
        if event.data2 != MIDI_OFF:
            COMMAND_HANDLER_MAP[event.data1](event)
    else:
        _printToLogs('ERROR', 'Unhandled command %d' % event.data1, event)


# Handles processing a midi event corresponding to a slider event.
def _handleSliderEvent(event, channel):
    value = event.data2
    _printToLogs('SLIDER%d : %d' % (channel, value), 'Event dispatched.', event)


def _getKnobDelta(event):
    value = event.data2
    return value if value < 64 else 64 - value


# Handles processing a midi event corresponding to a knob event.
def _handleKnobEvent(event):
    if event.data1 in KNOB_HANDLER_MAP:
        KNOB_HANDLER_MAP[event.data1](event, _getKnobDelta(event))
    else:
        _printToLogs('ERROR', "Unhandled knob %d" % event.data1, event)


def _onTransportsBack(event):
    _printToLogs('TransportsBack', 'Event dispatched', event)


def _onTransportsForward(event):
    _printToLogs('TransportsForward', 'Event dispatched', event)


def _onTransportsStop(event):
    _printToLogs('TransportsStop', 'Event dispatched', event)


def _onTransportsPausePlay(event):
    _printToLogs('TransportsPausePlay', 'Event dispatched', event)


def _onTransportsRecord(event):
    _printToLogs('TransportsRecord', 'Event dispatched', event)


def _onTransportsLoop(event):
    _printToLogs('TransportsLoop', 'Event dispatched', event)


def _onGlobalSave(event):
    _printToLogs('GlobalSave', 'Event dispatched', event)


def _onGlobalIn(event):
    _printToLogs('GlobalIn', 'Event dispatched', event)


def _onGlobalOut(event):
    _printToLogs('GlobalOut', 'Event dispatched', event)


def _onGlobalMetro(event):
    _printToLogs('GlobalMetro', 'Event dispatched', event)


def _onGlobalUndo(event):
    _printToLogs('GlobalUndo', 'Event dispatched', event)


def _onTrackSolo(event, track):
    _printToLogs('TrackSolo%d' % track, 'Event dispatched', event)


def _onTrackMute(event, track):
    _printToLogs('TrackMute%d' % track, 'Event dispatched', event)


def _onTrackRecord(event, track):
    _printToLogs('TrackRecord%d' % track, 'Event dispatched', event)


def _onTrackRead(event):
    _printToLogs('TrackRead', 'Event dispatched', event)


def _onTrackWrite(event):
    _printToLogs('TrackWrite', 'Event dispatched', event)


def _onNavigationLeft(event):
    _printToLogs('NavigationLeft', 'Event dispatched', event)


def _onNavigationRight(event):
    _printToLogs('NavigationRight', 'Event dispatched', event)


def _onBankNext(event):
    _printToLogs('BankNext', 'Event dispatched', event)


def _onBankPrevious(event):
    _printToLogs('BankPrevious', 'Event dispatched', event)


def _onLivePart1(event):
    _printToLogs('LivePart1', 'Event dispatched', event)


def _onLivePart2(event):
    _printToLogs('LivePart2', 'Event dispatched', event)


def _onBankSelect(event, track):
    _printToLogs('BankSelect%d' % track, 'Event dispatched', event)


def _onSetActiveTrack(event, track):
    global _activeTrack
    # Ignore the off message
    if event.data2 == MIDI_ON:
        _activeTrack = track
        _printToLogs('SetActiveTrack', 'Active track set to %d' % track, event)


def _onKnobPan(event, delta, index):
    _printToLogs('OnKnobPan%d : %d' % (index, delta), 'Event dispatched', event)


def _onKnobNavigation(event, delta):
    _printToLogs('OnKnobNavigation : %d' % delta, 'Event dispatched', event)


def _eventAsString(eventData):
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
    _setDisplay(line1='Hello', line2='World')

def OnMidiMsg(event):
    eventStr = _eventAsString(event)
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
    _setDisplay(line1='Hello', line2='World')

def OnUpdateBeatIndicator(event):
    print('OnUpdateBeatIndicator')
