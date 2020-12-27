# name=Arturia Keylab mkII (MIDI)
import device

from debug import log
# --------------------[ MIDI Script Integration Events for FL Studio ]---------------------------
# When "Analog Lab" mode is selected, MIDI commands for keys related to Analog Lab are sent here.
# All buttons have status code 176. These just need to be re-routed to the Analog Lab plugin
# Unfortunately, the only way to properly do this is to have the user manually configure the plugin to a free midiIn
# port number and forward the notes there.

def OnInit():
    print('Loaded MIDI script for Arturia Keylab mkII MIDI')

def OnMidiMsg(event):
    if event.status == 176:
        if event.data1 == 118 and event.data2 == 127:
            # User switched to Analog Lab mode.
            log('analoglab', 'Switched to Analog Lab.')

        portNum = 10
        message = event.status + (event.data1 << 8) + (event.data2 << 16) + (portNum << 24)
        device.forwardMIDICC(message, 2)
        log('analoglab', 'Forwarded status: %d, data1: %d, data2: %d' % (event.status, event.data1, event.data2))
        # Don't suppress sustain pedal
        if event.data1 != 64:
            event.handled = True

