# name=Arturia Keylab mkII DAW (MIDIIN2/MIDIOUT2)
# url=https://github.com/rjuang/flstudio-arturia-keylab-mk2
# receiveFrom=Arturia Keylab mkII (MIDI)
from arturia import ArturiaController
from arturia_processor import ArturiaMidiProcessor

import arturia_midi


WELCOME_DISPLAY_INTERVAL_MS = 1500

# --------------------[ Global state for MIDI Script ] ------------------------------------------

_controller = ArturiaController()
_processor = ArturiaMidiProcessor(_controller)
_payload_buffer = []

# --------------------[ MIDI Script Integration Events for FL Studio ]---------------------------



def OnInit():
    global _controller
    print('Loaded MIDI script for Arturia Keylab mkII')
    _controller.Sync(0xFFFF)
    _controller.paged_display().SetPageLines('welcome', line1='Connected to ', line2='   FL Studio')
    _controller.paged_display().SetActivePage('main')
    _controller.paged_display().SetActivePage('welcome', expires=WELCOME_DISPLAY_INTERVAL_MS)


def OnIdle():
    _controller.Idle()


def OnMidiMsg(event):
    global _payload_buffer, _processor
    if event.status == arturia_midi.INTER_SCRIPT_STATUS_BYTE:
        if event.data1 == arturia_midi.INTER_SCRIPT_DATA1_BEGIN_PAYLOAD_CMD:
            _payload_buffer = []
        elif event.data1 == arturia_midi.INTER_SCRIPT_DATA1_END_PAYLOAD_CMD:
            arturia_midi.send_to_device(_payload_buffer)
            _payload_buffer = []
        elif event.data1 == arturia_midi.INTER_SCRIPT_DATA1_UPDATE_STATE:
            if event.data2 == arturia_midi.INTER_SCRIPT_DATA2_STATE_PAD_RECORD_START:
                _processor.NotifyPadRecordingState(True)
            elif event.data2 == arturia_midi.INTER_SCRIPT_DATA2_STATE_PAD_RECORD_STOP:
                _processor.NotifyPadRecordingState(False)
        event.handled = True
    elif event.status == arturia_midi.PAYLOAD_STATUS_BYTE:
        _payload_buffer.append(event.data1)
        _payload_buffer.append(event.data2)
        event.handled = True
    else:
        if _processor.ProcessEvent(event):
            event.handled = True
        _controller.RefreshDisplay()


def OnRefresh(flags):
    _controller.Sync(flags)


def OnUpdateBeatIndicator(value):
    _controller.metronome().ProcessBeat(value)
