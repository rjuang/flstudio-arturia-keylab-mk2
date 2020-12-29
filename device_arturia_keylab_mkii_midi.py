# name=Arturia Keylab mkII (MIDI)
import channels
import device

from arturia_leds import ArturiaLights
from arturia_scheduler import Scheduler
from arturia_recorder import Recorder
from arturia_savedata import SaveData

from debug import log
# --------------------[ MIDI Script Integration Events for FL Studio ]---------------------------
# When "Analog Lab" mode is selected, MIDI commands for keys related to Analog Lab are sent here.
# All buttons have status code 176. These just need to be re-routed to the Analog Lab plugin
# Unfortunately, the only way to properly do this is to have the user manually configure the plugin to a free midiIn
# port number and forward the notes there.

MIDI_DRUM_PAD_STATUS_ON = 169
MIDI_DRUM_PAD_STATUS_OFF = 137
MIDI_DRUM_PAD_DATA1_MIN = 36
MIDI_DRUM_PAD_DATA1_MAX = 51

_scheduler = Scheduler()
_savedata = SaveData()
_recorder = Recorder(_scheduler, _savedata)
_lights = ArturiaLights()

_pad_recording_led = False
_pad_recording_task = None
_sustain_enabled = False
_fallback_pad_values = {}
_longpress_status = {}


def OnInit():
    print('Loaded MIDI script for Arturia Keylab mkII MIDI')


def OnRefresh(flags):
    _savedata.Load()


def OnShortPressDrumPad(event):
    global _pad_recording_task
    note = event.data1
    if _recorder.IsRecording():
        log('midi', 'Stop Recording. short press detected for %s' % str(note))
        _recorder.StopRecording()
        _scheduler.CancelTask(_pad_recording_task)
        _pad_recording_task = None
    else:
        global _sustain_enabled
        log('midi', 'Play. short press detected for %s. Sustain=%s' % (str(note), _sustain_enabled))
        if not _recorder.Play(note, loop=_sustain_enabled):
            channels.midiNoteOn(channels.selectedChannel(), note, _fallback_pad_values[note])


def OnLongPressDrumPad(note):
    global _pad_recording_led
    if _recorder.IsRecording():
        log('midi', 'Stop Recording. Long press detected for %s' % str(note))
        _recorder.StopRecording()
    else:
        log('midi', 'Start Recording. Long press detected for %s' % str(note))
        _recorder.StartRecording(note)
        _pad_recording_led = False
        BlinkLight(note)


def BlinkLight(note):
    global _pad_recording_led, _pad_recording_task
    if _recorder.IsRecording():
        led_id = note - MIDI_DRUM_PAD_DATA1_MIN + ArturiaLights.ID_PAD_R1_C1
        _pad_recording_led = not _pad_recording_led
        _lights.SetLights({led_id: ArturiaLights.AsOnOffByte(_pad_recording_led)})
        _pad_recording_task = _scheduler.ScheduleTask(lambda: BlinkLight(note), delay=1000)

def OnMidiMsg(event):
    note = event.data1
    if event.status == MIDI_DRUM_PAD_STATUS_ON or event.status == 153:
        if MIDI_DRUM_PAD_DATA1_MIN <= note <= MIDI_DRUM_PAD_DATA1_MAX:
            event.handled = True
            if event.status == 153:
                _fallback_pad_values[event.data1] = event.data2
            if note not in _longpress_status:
                log('midi', 'Schedule long press detection for %s' % str(note))
                _longpress_status[note] = _scheduler.ScheduleTask(lambda: OnLongPressDrumPad(note), delay=1000)

    elif event.status == MIDI_DRUM_PAD_STATUS_OFF:
        if MIDI_DRUM_PAD_DATA1_MIN <= event.data1 <= MIDI_DRUM_PAD_DATA1_MAX:
            event.handled = True
            if event.data1 in _longpress_status:
                if _scheduler.CancelTask(_longpress_status[event.data1]):
                    log('midi', 'Long press canceled for %s' % str(event.data1))
                    OnShortPressDrumPad(event)
                del _longpress_status[event.data1]

    elif event.status == 176:
        if event.data1 == 118 and event.data2 == 127:
            # User switched to Analog Lab mode.
            log('analoglab', 'Switched to Analog Lab.')

        portNum = 10
        message = event.status + (event.data1 << 8) + (event.data2 << 16) + (portNum << 24)
        device.forwardMIDICC(message, 2)

        if event.data1 == 64:
            global _sustain_enabled
            _sustain_enabled = (event.data2 == 127)

        # Don't suppress sustain pedal
        if event.data1 != 64:
            event.handled = True
    elif event.status == 144:  # Midi note on
        _recorder.OnMidiNote(event)

    log('midi', 'status: %d, data1: %d, data2: %d handled: %s' % (event.status, event.data1, event.data2, str(event.handled)))


def OnIdle():
    _scheduler.Idle()
