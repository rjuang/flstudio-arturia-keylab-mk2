from arturia_leds import ArturiaLights

import config
import playlist
import ui


class VisualMetronome:
    """ Manages animating button lights when song/pattern is playing so that user has a visual metronome. """
    def __init__(self, lights):
        self._beat_count = 0
        self._bar_count = -1  # First beat is always a bar, so this needs to get incremented to 0
        self._lights = lights
        self._last_bst_position = (1, 0, 1)

    def Reset(self):
        """ Resets the metronome so that it begins from a rewinded playback state. """
        self._beat_count = 0
        self._bar_count = -1
        # Also turn off all lights
        self._lights.SetPadLights(ArturiaLights.ZeroMatrix())
        self._lights.SetLights({
            ArturiaLights.ID_TRANSPORTS_REWIND: ArturiaLights.LED_OFF,
            ArturiaLights.ID_TRANSPORTS_FORWARD: ArturiaLights.LED_OFF,
        })

    def ProcessBeat(self, value):
        """ Notify the metronome that a beat occured (e.g. OnUpdateBeatIndicator). """
        if config.METRONOME_LIGHTS_ONLY_WHEN_METRONOME_ENABLED and not ui.isMetronomeEnabled():
            # Disable metronome if configured to correlate to metronome toggle and is disabled.
            return

        lights = ArturiaLights.ZeroMatrix()
        current_bst_position = (playlist.getVisTimeBar(),
                                playlist.getVisTimeStep(),
                                playlist.getVisTimeTick())
        if current_bst_position < self._last_bst_position:
            self.Reset()

        self._last_bst_position = current_bst_position

        if value == 2:
            # Indicates regular beat
            self._beat_count += 1

        if value == 1:
            # Indicates beat at a bar
            self._beat_count = 0
            self._bar_count += 1

        num_rows = len(lights)
        num_cols = len(lights[0])
        if value != 0:
            row = self._bar_count % num_rows
            col = self._beat_count % num_cols
            lights[row][col] = ArturiaLights.LED_ON
            two_step = self._beat_count % 2 == 0

            if config.ENABLE_PAD_METRONOME_LIGHTS:
                self._lights.SetPadLights(lights)

            if config.ENABLE_TRANSPORTS_METRONOME_LIGHTS:
                self._lights.SetLights({
                    ArturiaLights.ID_TRANSPORTS_REWIND: ArturiaLights.AsOnOffByte(two_step),
                    ArturiaLights.ID_TRANSPORTS_FORWARD: ArturiaLights.AsOnOffByte(not two_step),
                })
