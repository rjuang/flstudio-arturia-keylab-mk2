from arturia_midi import send_to_device

import config
import device
import time
import utils

ESSENTIAL_KEYBOARD = 'mkII' not in device.getName()
MKII_88_KEYBOARD = 'mkII 88' in device.getName()
MKII_49_KEYBOARD = 'mkII 49' in device.getName()


class ArturiaLights:
    """Maintains setting all the button lights on the Arturia device."""
    # Value for turning on an LED.
    LED_ON = 127
    # Value for turning off an LED.
    LED_OFF = 0

    MISSING = 0

    # IDs for all of the buttons with lights.
    ID_OCTAVE_MINUS = 16
    ID_OCTAVE_PLUS = 17
    ID_CHORD = 18
    ID_TRANSPOSE = 19
    ID_MIDI_CHANNEL = 20
    ID_PAD_MODE_CHORD_TRANSPOSE = 21
    ID_PAD_MODE_CHORD_MEMORY = 22
    ID_PAD_MODE_PAD = 23
    ID_NAVIGATION_CATEGORY = 24
    ID_NAVIGATION_PRESET = 25
    ID_NAVIGATION_LEFT = 26
    ID_NAVIGATION_RIGHT = 27
    ID_NAVIGATION_ANALOG_LAB = 28
    ID_NAVIGATION_DAW = 29
    ID_NAVIGATION_USER = 30
    ID_BANK_NEXT = 31
    ID_BANK_PREVIOUS = 32
    ID_BANK_TOGGLE = 33

    # Program bank buttons (these are the channel select buttons). Last button is the master/multi button
    ARRAY_IDS_BANK_SELECT = [34, 35, 36, 37, 38, 39, 40, 41, 42]

    # Track controls
    ID_TRACK_SOLO = 96
    ID_TRACK_MUTE = 97
    ID_TRACK_RECORD = 98
    ID_TRACK_READ = 99
    ID_TRACK_WRITE = 100

    # Global controls
    ID_GLOBAL_SAVE = 101
    ID_GLOBAL_IN = 102
    ID_GLOBAL_OUT = 103
    ID_GLOBAL_METRO = 104
    ID_GLOBAL_UNDO = 105

    # Transports section
    ID_TRANSPORTS_REWIND = 106
    ID_TRANSPORTS_FORWARD = 107
    ID_TRANSPORTS_STOP = 108
    ID_TRANSPORTS_PLAY = 109
    ID_TRANSPORTS_RECORD = 110
    ID_TRANSPORTS_LOOP = 111

    # 4x4 lookup for the pad ids.
    MATRIX_IDS_PAD = [
        [112, 113, 114, 115],
        [116, 117, 118, 119],
        [120, 121, 122, 123],
        [124, 125, 126, 127],
    ]

    # Command bytes for setting monochrome light (followed by id, 7-bit LED value)
    SET_MONOCHROME_LIGHT_COMMAND = bytes([0x02, 0x00, 0x10])

    # Command bytes for setting RGB light (followed by id, 7-bit R, 7-bit G, 7-bit B)
    SET_RGB_LIGHT_COMMAND = bytes([0x02, 0x00, 0x16])

    if ESSENTIAL_KEYBOARD:
        # Override LED code for essential keyboard
        ID_OCTAVE_MINUS = 58
        ID_OCTAVE_PLUS = 59
        ID_CHORD = 56
        ID_TRANSPOSE = 57
        ID_MIDI_CHANNEL = 61

        ID_PAD_MODE_CHORD_TRANSPOSE = MISSING
        ID_PAD_MODE_CHORD_MEMORY = MISSING

        ID_PAD_MODE_PAD = 60

        ID_NAVIGATION_CATEGORY = 22
        ID_NAVIGATION_PRESET = 23
        ID_NAVIGATION_LEFT = 24
        ID_NAVIGATION_RIGHT = 25

        ID_NAVIGATION_ANALOG_LAB = MISSING
        ID_NAVIGATION_DAW = MISSING
        ID_NAVIGATION_USER = MISSING

        ID_BANK_NEXT = 26
        ID_BANK_PREVIOUS = 27
        ID_BANK_TOGGLE = 28

        ARRAY_IDS_BANK_SELECT = []

        # Track controls
        ID_TRACK_SOLO = MISSING
        ID_TRACK_MUTE = MISSING
        ID_TRACK_RECORD = MISSING
        ID_TRACK_READ = MISSING
        ID_TRACK_WRITE = MISSING

        # Global controls
        ID_GLOBAL_SAVE = 86
        ID_GLOBAL_IN = 88
        ID_GLOBAL_OUT = MISSING
        ID_GLOBAL_METRO = 89
        ID_GLOBAL_UNDO = 87

        # Transports section
        ID_TRANSPORTS_REWIND = 91
        ID_TRANSPORTS_FORWARD = 92
        ID_TRANSPORTS_STOP = 93
        ID_TRANSPORTS_PLAY = 94
        ID_TRANSPORTS_RECORD = 95
        ID_TRANSPORTS_LOOP = 90
        MATRIX_IDS_PAD = [
            [32, 35, 38, 41],
            [44, 47, 50, 53],
        ]

    def __init__(self, send_fn=None):
        if send_fn is None:
            send_fn = send_to_device
        self._send_fn = send_fn

        # Map of last send times
        self._last_send_ms = {}

    @staticmethod
    def AsOnOffByte(is_on):
        """Converts a boolean to the corresponding on/off to use in the method calls of this class."""
        return ArturiaLights.LED_ON if is_on else ArturiaLights.LED_OFF

    @staticmethod
    def ZeroMatrix(zero=0):
        num_rows = len(ArturiaLights.MATRIX_IDS_PAD)
        num_cols = len(ArturiaLights.MATRIX_IDS_PAD[0])
        return [[zero]*num_cols for _ in range(num_rows)]

    @staticmethod
    def rgb2int(red, green, blue):
        bitmask = 0xFF
        red &= bitmask
        green &= bitmask
        blue &= bitmask
        return (red << 16) | (green << 8) | blue

    @staticmethod
    def int2rgb(value):
        bitmask = 0xFF
        red = (value >> 16) & bitmask
        green = (value >> 8) & bitmask
        blue = value & bitmask
        return red, green, blue

    @staticmethod
    def to7bit(value):
        return int(float(value) * (127.0 / 255.0))

    @staticmethod
    def to7bitColor(color):
        r, g, b = ArturiaLights.int2rgb(color)
        r = ArturiaLights.to7bit(r)
        g = ArturiaLights.to7bit(g)
        b = ArturiaLights.to7bit(b)
        return ArturiaLights.rgb2int(r, g, b)

    @staticmethod
    def mapToClosestHue(rgb, sat=0.7, value=0.02, maxrgb=127):
        h, _, _ = utils.RGBToHSVColor(rgb)
        s = sat
        v = value
        r, g, b = utils.HSVtoRGB(h, s, v)
        return ArturiaLights.rgb2int(int(maxrgb*r), int(maxrgb*g), int(maxrgb*b))

    @staticmethod
    def fadedColor(rgb):
        return ArturiaLights.mapToClosestHue(rgb, sat=1.0, value=0.02, maxrgb=127)

    @staticmethod
    def fullColor(rgb):
        return ArturiaLights.mapToClosestHue(rgb, sat=1.0, value=0.2, maxrgb=127)

    @staticmethod
    def getPadLedId(button_id):
        MIDI_DRUM_PAD_DATA1_MIN = 36

        if MKII_88_KEYBOARD or MKII_49_KEYBOARD or config.INVERT_LED_LAYOUT:
            # On 49/88 keyboard, the button IDs are flipped:
            # 0x30, 0x31, 0x32, 0x33
            # 0x2C, 0x2D, 0x2E, 0x2F
            # 0x28, 0x29, 0x30, 0x31
            # 0x24, 0x25, 0x26, 0x27
            idx = button_id - MIDI_DRUM_PAD_DATA1_MIN
            col = idx % 4
            row = 3 - (idx // 4)
            return ArturiaLights.MATRIX_IDS_PAD[row][col]
        return button_id - MIDI_DRUM_PAD_DATA1_MIN + ArturiaLights.MATRIX_IDS_PAD[0][0]


    def SetPadLights(self, matrix_values, rgb=False):
        """ Set the pad lights given a matrix of color values to set the pad with.
        :param matrix_values: 4x4 array of arrays containing the LED color values.
        """
        # Note: Pad lights can be set to RGB colors, but this doesn't seem to be working.
        led_map = {}
        num_rows = len(ArturiaLights.MATRIX_IDS_PAD)
        num_cols = len(ArturiaLights.MATRIX_IDS_PAD[0])
        for r in range(num_rows):
            for c in range(num_cols):
                led_map[ArturiaLights.MATRIX_IDS_PAD[r][c]] = matrix_values[r][c]
        self.SetLights(led_map, rgb=rgb)

    def SetBankLights(self, array_values, rgb=False):
        """ Set the bank lights given an array of color values to set the bank lights with.

        :param array_values: a 9-element array containing the LED color values.
        """
        if not ArturiaLights.ARRAY_IDS_BANK_SELECT:
            return

        led_map = {k: v for k, v in zip(ArturiaLights.ARRAY_IDS_BANK_SELECT, array_values)}
        self.SetLights(led_map, rgb=rgb)

    def SetLights(self, led_mapping, rgb=False):
        """ Given a map of LED ids to color value, construct and send a command with all the led mapping. """
        time_ms = time.monotonic() * 1000
        for led_id, led_value in led_mapping.items():
            if led_id == ArturiaLights.MISSING:
                # Do not toggle/set lights that are missing
                continue
            if led_id not in self._last_send_ms:
                self._last_send_ms[led_id] = 0

            if time_ms - self._last_send_ms[led_id] < 33:
                # Drop value
                continue
            self._last_send_ms[led_id] = time_ms
            if rgb:
                r, g, b = ArturiaLights.int2rgb(led_value)
                self._send_fn(ArturiaLights.SET_RGB_LIGHT_COMMAND + bytes([led_id, r, g, b]))
            else:
                self._send_fn(ArturiaLights.SET_MONOCHROME_LIGHT_COMMAND + bytes([led_id, led_value]))
            # Need to intentionally sleep to allow time for keyboard to process command sent.
            time.sleep(0.0001)
