import channels
import general
import midi
import ui

from arturia_display import ArturiaDisplay
from arturia_leds import ArturiaLights
from debug import log

class ArturiaInputControls:
    """ Manges what the sliders/knobs control on an Arturia Keyboard.

     On the Arturia KeyLab 61 Keyboard, there is a row of 9 encoders and 9 sliders. Plugins may have
     more than 9 encoders/sliders. As such, we will allow mapping the Next/Previous buttons to
     different "pages".
     """

    @staticmethod
    def _plugin_rec_fn(idx):
        return lambda: channels.getRecEventId(channels.selectedChannel()) + midi.REC_Chan_Plugin_First + idx

    @staticmethod
    def _plugin_map_for(offsets):
        return [ArturiaInputControls._plugin_rec_fn(x) for x in offsets]

    def __init__(self, paged_display, lights):
        self._paged_display = paged_display
        self._lights = lights

        # Maps a string containing the plugin name to an array of lambda functions containing
        # page knob. Because there may be more knobs on the

        # Some notes
        # For FLEX plugin:
        # midi.REC_Chan_Plugin_First:
        #  Vol Envelope : +0 - +4 -> A, H, D, S, R
        #  Filter Envelope: ++5 -> +9 -> A, H , D, S, R
        #  Sliders: +10, -> +17
        # FCutoff: +18,
        # Env Amt: +19
        # Env Res: +20
        # Master filter cutoff: +21
        # Master res : 22
        # Delay - mix - 25
        # Delay - time - 26
        # Delay - feedback 27
        # Delay - mod - 28
        # Delay - color - 29
        # Reverb - mix - 30
        # Reverb - decay - 31
        # Reverb - size - 32
        # Reverb - Mod - 33
        # Reverb - Color - 34
        # Limiter - Pre Vol - 35
        # Output volume - 36
        # Delay ON/Off - 37
        # Reverb ON/Off- 38
        # Pitch - 39
        # Master Filter ON/OFF -40
        # Limiter ON/OFF 41
        # LMH Mix -42
        # Limiter Type - 43
        # Reverb Mod Speed 44
        #
        self._knobs_map = {
            # Default mapping. Sequential. Good for debugging
            '': [
                self._plugin_map_for(range(0, 9)),
                self._plugin_map_for(range(9, 18)),
                self._plugin_map_for(range(18, 27)),
                self._plugin_map_for(range(27, 36)),
                self._plugin_map_for(range(36, 45)),
                self._plugin_map_for(range(45, 54)),
                self._plugin_map_for(range(54, 63)),
                self._plugin_map_for(range(63, 72)),
            ],

            # Mapping for FLEX plugin
            'FLEX': [
                # Sliders 1-8, Output Volume
                self._plugin_map_for([10, 11, 12, 13, 14, 15, 16, 17, 36]),
                # Filter knobs, Filter Env AHDSR
                self._plugin_map_for([18, 20, 19, 5, 6, 7, 8, 9, 39]),
                # Master knobs + type,  Volume Env AHDSR, Master ON/OFF
                self._plugin_map_for([21, 22, 23, 0, 1, 2, 3, 4, 40]),
                # Delay buttons
                self._plugin_map_for([25, 26, 27, 29, 28, 24, 37, 37, 37]),
                # Reverb buttons
                self._plugin_map_for([30, 31, 32, 34, 33, 44, 38, 38, 38]),
                # Limiter
                self._plugin_map_for([35, 42, 43, 41, 41, 41, 41, 41, 41]),
            ],
        }

        self._sliders_map = {
            '': [],
        }

        self._knobs_mode = ''
        self._knobs_mode_index = 0
        self._sliders_mode = ''
        self._sliders_mode_index = 0
        self._last_hint_title = ''

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

    def SetKnobMode(self, knob_mode):
        if knob_mode not in self._knobs_map:
            knob_mode = ''
            log('WARNING', 'No encoder mapping for plugin "%s"' % knob_mode)
        self._knobs_mode = knob_mode
        self._knobs_mode_index = 0
        return self

    def SetSliderMode(self, slider_mode):
        self._sliders_mode = slider_mode
        self._sliders_mode_index = 0
        return self

    def _get_knob_pages(self):
        knob_key = self._knobs_mode
        if knob_key not in self._knobs_mode:
            # Knobs don't do anything
            log('knobs', 'Invalid log mode %s' % knob_key)
            return []
        return self._knobs_map[knob_key]

    def NextKnobsPage(self):
        num_pages = len(self._get_knob_pages())
        if num_pages == 0:
            return
        self._knobs_mode_index = (self._knobs_mode_index + 1) % num_pages
        self._update_lights()
        self._display_hint(' Knobs Mapping', '     %d of %d' % (self._knobs_mode_index + 1, num_pages))
        return self

    def NextSlidersPage(self):
        self._update_lights()
        pass

    def ProcessKnobInput(self, knob_index, delta):
        pages = self._get_knob_pages()

        if len(pages) == 0:
            # Knob mode is invalid
            self._display_unset_knob()
            return

        # Assume index is always valid
        knobs = pages[self._knobs_mode_index]

        # Check if knob is mapped
        if knob_index >= len(knobs):
            # Knob is unmapped in the array
            self._display_unset_knob()
            return

        event_id = knobs[knob_index]()
        value = channels.incEventValue(event_id, delta, 0.01)
        general.processRECEvent(event_id, value, midi.REC_UpdateValue | midi.REC_UpdatePlugLabel | midi.REC_ShowHint)
        self._check_and_show_hint()
        return self

    def ProcessSliderInput(self, slider_index, delta):
        #event_id = self._sliders_base_event() + self._sliders_offset + slider_index
        #value = channels.incEventValue(event_id, delta, 0.01)
        #general.processRECEvent(event_id, value, midi.REC_UpdateValue)
        #self._check_and_show_hint()
        return self

    def Refresh(self):
        self._update_lights()

    def _display_hint(self, hint_title, hint_value):
        hint_title = ArturiaDisplay.abbreviate(hint_title.upper())
        hint_value = hint_value.upper()

        if self._last_hint_title != hint_title:
            self._paged_display.display().ResetScroll()

        self._last_hint_title = hint_title
        self._paged_display.SetPageLines('hint', line1=hint_title, line2=hint_value)
        self._paged_display.SetActivePage('hint', expires=5000)

    def _display_unset_knob(self):
        self._display_hint(' (KNOB UNSET) ', ' ')

    def _check_and_show_hint(self):
        hint = ui.getHintMsg()
        if not hint:
            return

        lines = hint.split(':', 1)
        if len(lines) == 1:
            lines.append(' ')
        self._display_hint(lines[0], lines[1])

    def _get_pad_position(self, index):
        return int(index / 4) % 2, index % 4

    def _update_lights(self):
        # Set 4x4 Pad lights to indicate the current configuration
        pad_values = ArturiaLights.Zero4x4Matrix()

        knob_row, knob_col = self._get_pad_position(self._knobs_mode_index)
        slider_row, slider_col = self._get_pad_position(self._sliders_mode_index)
        pad_values[knob_row][knob_col] = ArturiaLights.LED_ON
        pad_values[slider_row + 2][slider_col] = ArturiaLights.LED_ON
        self._lights.SetPadLights(pad_values)
