# name=Arturia Keylab mkII DAW (MIDIIN2/MIDIOUT2)
from arturia import ArturiaController
from arturia_processor import ArturiaMidiProcessor

WELCOME_DISPLAY_INTERVAL_MS = 1500

# --------------------[ Global state for MIDI Script ] ------------------------------------------

_controller = ArturiaController()
_processor = ArturiaMidiProcessor(_controller)

# --------------------[ MIDI Script Integration Events for FL Studio ]---------------------------

def OnInit():
    global _controller
    print('Loaded MIDI script for Arturia Keylab mkII')
    _controller.Sync()
    _controller.paged_display().SetPageLines('welcome', line1='Connected to ', line2='   FL Studio')
    _controller.paged_display().SetActivePage('main')
    _controller.paged_display().SetActivePage('welcome', expires=WELCOME_DISPLAY_INTERVAL_MS)


def OnIdle():
    _controller.Idle()


def OnMidiMsg(event):
    if _processor.ProcessEvent(event):
        event.handled = True


def OnRefresh(flags):
    _controller.Sync()


def OnUpdateBeatIndicator(value):
    _controller.metronome().ProcessBeat(value)
