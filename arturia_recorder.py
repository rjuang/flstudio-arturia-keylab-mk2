import channels
import time

from debug import log

class Recorder:
    """MIDI Sequence recorder and playback."""
    def __init__(self, scheduler):
        self._scheduler = scheduler

        # List of tuples containing (time, channel note, velocity)
        self._events = {}
        self._channels = {}
        self._recording = None

    def OnMidiNote(self, event):
        recording_key = self._recording
        if recording_key is None:
            # Don't process any notes if we are not recording
            return
        timestamp = int(round(time.time() * 1000))
        channel = channels.selectedChannel()
        # In case channel switching occurs, or multi-devices recording to different notes, make sure to record this.
        if recording_key not in self._channels:
            self._channels[recording_key] = set()
        self._channels[recording_key].add(channel)
        if recording_key not in self._events:
            self._events[recording_key] = []
        self._events[recording_key].append((timestamp, channel, event.note, event.velocity))

    def StartRecording(self, key):
        self._recording = key
        self._events[key] = []
        self._channels[key] = set()
        log('recorder', 'Start recording: %s' % str(self._recording))

    def StopRecording(self):
        log('recorder', 'Stop recording: %s' % str(self._recording))
        self._recording = None

    def IsRecording(self):
        return self._recording is not None

    def _ScheduleNote(self, channel, note, velocity, delay_ms):
        self._scheduler.ScheduleTask(lambda: channels.midiNoteOn(channel, note, velocity), delay=delay_ms)

    def Play(self, key):
        # Make sure all channels are selected
        if key not in self._events or not self._events[key]:
            # Nothing recorded for playback so return.
            return False

        timestamp_base = self._events[key][0][0]
        for timestamp, channel, note, velocity in self._events[key]:
            delay_ms = timestamp - timestamp_base
            if delay_ms <= 0:
                # Play now
                channels.midiNoteOn(channel, note, velocity)
            else:
                # Schedule for playback later
                self._ScheduleNote(channel, note, velocity, delay_ms)
        return True