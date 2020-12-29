import channels
import time

from debug import log

class Recorder:
    """MIDI Sequence recorder and playback."""
    def __init__(self, scheduler, savedata):
        self._scheduler = scheduler

        # List of tuples containing (time, channel note, velocity)
        self._recording = None
        self._savedata = savedata

    def OnMidiNote(self, event):
        recording_key = self._recording
        if recording_key is None:
            # Don't process any notes if we are not recording
            return
        timestamp = int(round(time.time() * 1000))
        channel = channels.selectedChannel()
        self._savedata.Get(recording_key).extend([timestamp, channel, event.note, event.velocity])

    def StartRecording(self, key):
        self._recording = str(key)
        # Make sure to clear the previous data on new recording
        self._savedata.Put(self._recording, [])
        log('recorder', 'Start recording: %s' % str(self._recording))

    def StopRecording(self):
        log('recorder', 'Stop recording: %s' % str(self._recording))
        self._recording = None
        self._savedata.Commit()

    def IsRecording(self):
        return self._recording is not None

    def _ScheduleNote(self, channel, note, velocity, delay_ms):
        self._scheduler.ScheduleTask(lambda: channels.midiNoteOn(channel, note, velocity), delay=delay_ms)

    def Play(self, key):
        # Make sure all channels are selected
        values = self._savedata.Get(str(key))
        if not values:
            return False
        timestamp_base = values[0]
        for i in range(0, len(values), 4):
            timestamp, channel, note, velocity = values[i:i+4]
            delay_ms = timestamp - timestamp_base
            if delay_ms <= 0:
                # Play now
                channels.midiNoteOn(channel, note, velocity)
            else:
                # Schedule for playback later
                self._ScheduleNote(channel, note, velocity, delay_ms)
        return True