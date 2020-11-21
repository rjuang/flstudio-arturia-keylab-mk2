import channels
import general
import midi

class ArturiaInputControls:
    """ Manges what the sliders/knobs control on an Arturia Keyboard. """
    def __init__(self):
        self._knobs_base_fn = lambda: channels.getRecEventId(channels.selectedChannel()) + midi.REC_Chan_Plugin_First
        self._knobs_offset = 0

        self._sliders_base_fn = lambda: channels.getRecEventId(channels.selectedChannel()) + midi.REC_Chan_Plugin_First
        self._sliders_offset = 0

    def SetKnobs(self, base_fn=None, offset=None):
        if base_fn is not None:
            self._knobs_base_fn = base_fn
        if offset is not None:
            self._knobs_offset = offset
        return self

    def SetSliders(self, base_fn=None, offset=None):
        if base_fn is not None:
            self._sliders_base_fn = base_fn
        if offset is not None:
            self._sliders_offset = offset
        return self

    def GetKnobsSettings(self):
        return self._knobs_base_fn, self._knobs_offset

    def GetSlidersSettings(self):
        return self._sliders_base_fn, self._sliders_offset

    def ProcessKnobInput(self, knob_index, delta):
        event_id = self._knobs_base_event() + self._knobs_offset + knob_index
        value = channels.incEventValue(event_id, delta, 0.01)
        general.processRECEvent(event_id, value, midi.REC_UpdateValue)
        return self

    def ProcessSliderInput(self, slider_index, delta):
        event_id = self._sliders_base_event() + self._sliders_offset + slider_index
        value = channels.incEventValue(event_id, delta, 0.01)
        general.processRECEvent(event_id, value, midi.REC_UpdateValue)
        return self