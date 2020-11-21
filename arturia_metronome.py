from arturia_leds import ArturiaLights


class VisualMetronome:
    """ Manages animating button lights when song/pattern is playing so that user has a visual metronome. """
    def __init__(self, lights):
        self._beat_count = 0
        self._bar_count = -1  # First beat is always a bar, so this needs to get incremented to 0
        self._lights = lights

    def Reset(self):
        """ Resets the metronome so that it begins from a rewinded playback state. """
        self._beat_count = 0
        self._bar_count = -1
        # Also turn off all lights
        self._lights.SetPadLights(ArturiaLights.Zero4x4Matrix())
        self._lights.SetLights({
            ArturiaLights.ID_TRANSPORTS_REWIND: ArturiaLights.LED_OFF,
            ArturiaLights.ID_TRANSPORTS_FORWARD: ArturiaLights.LED_OFF,
        })

    def ProcessBeat(self, value):
        """ Notify the metronome that a beat occured (e.g. OnUpdateBeatIndicator). """
        lights = ArturiaLights.Zero4x4Matrix()
        if value == 2:
            # Indicates regular beat
            self._beat_count += 1

        if value == 1:
            # Indicates beat at a bar
            self._beat_count = 0
            self._bar_count += 1

        if value != 0:
            row = self._bar_count % 4
            col = self._beat_count % 4
            lights[row][col] = ArturiaLights.LED_ON
            two_step = self._beat_count % 2 == 0
            self._lights.SetPadLights(lights)
            self._lights.SetLights({
                ArturiaLights.ID_TRANSPORTS_REWIND: ArturiaLights.AsOnOffByte(two_step),
                ArturiaLights.ID_TRANSPORTS_FORWARD: ArturiaLights.AsOnOffByte(not two_step),
            })