import channels
import mixer
import time

from debug import log

class Recorder:
    """MIDI Sequence recorder and playback."""
    def __init__(self, scheduler, savedata):
        self._scheduler = scheduler

        # List of tuples containing (time, channel note, velocity)
        self._recording = None
        self._savedata = savedata
        self._looping = set()

    def OnMidiNote(self, event):
        recording_key = self._recording
        if recording_key is None:
            # Don't process any notes if we are not recording
            return
        timestamp = int(round(time.time() * 1000))
        channel = channels.selectedChannel()
        velocity = event.velocity
        if 128 <= event.status <= 143:   # Midi off event
            velocity = 0
        self._savedata.Get(recording_key).extend([timestamp, channel, event.note, velocity])

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

    def _SchedulePlay(self, key, values, check_looping=False):
        if check_looping and key not in self._looping:
            return

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

        if key in self._looping:
            # Make sure to schedule in a delay of one beat for the last note to finish playing. Otherwise, they will
            # overlap
            bpm = mixer.getCurrentTempo() / 1000
            beat_interval_ms = 60000 / bpm
            log('recorder', 'Scheduling loop for drum pattern=%d' % key)
            self._scheduler.ScheduleTask(lambda: self._SchedulePlay(key, values, check_looping=True),
                                         delay=delay_ms + beat_interval_ms)

    def Play(self, key, loop=False):
        log('recorder', 'Playing drum pattern for %s. Loop=%s' % (key, loop))
        # Make sure all channels are selected
        if key in self._looping:
            # Stop playing loop
            self._looping.remove(key)
            return True

        if loop:
            self._looping.add(key)

        values = self._savedata.Get(str(key))
        if not values:
            return False
        self._SchedulePlay(key, values)

        return True