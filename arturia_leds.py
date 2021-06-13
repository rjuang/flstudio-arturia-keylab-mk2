from arturia_midi import send_to_device

import device

ESSENTIAL_KEYBOARD = 'mkII' not in device.getName()


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

    @staticmethod
    def AsOnOffByte(is_on):
        """Converts a boolean to the corresponding on/off to use in the method calls of this class."""
        return ArturiaLights.LED_ON if is_on else ArturiaLights.LED_OFF

    @staticmethod
    def ZeroMatrix():
        num_rows = len(ArturiaLights.MATRIX_IDS_PAD)
        num_cols = len(ArturiaLights.MATRIX_IDS_PAD[0])
        return [[0]*num_cols for _ in range(num_rows)]

    def SetPadLights(self, matrix_values):
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
        self.SetLights(led_map)

    def SetBankLights(self, array_values):
        """ Set the bank lights given an array of color values to set the bank lights with.

        :param array_values: a 9-element array containing the LED color values.
        """
        if not ArturiaLights.ARRAY_IDS_BANK_SELECT:
            return

        led_map = {k: v for k, v in zip(ArturiaLights.ARRAY_IDS_BANK_SELECT, array_values)}
        self.SetLights(led_map)

    def SetLights(self, led_mapping):
        """ Given a map of LED ids to color value, construct and send a command with all the led mapping. """
        data = bytes([])
        for led_id, led_value in led_mapping.items():
            if led_id == ArturiaLights.MISSING:
                # Do not toggle/set lights that are missing
                continue
            data += bytes([led_id, led_value])
        self._send_fn(ArturiaLights.SET_MONOCHROME_LIGHT_COMMAND + data)
