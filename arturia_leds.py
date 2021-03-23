from arturia_midi import send_to_device


class ArturiaLights:
    """Maintains setting all the button lights on the Arturia device."""

    # Value for turning on an LED.
    LED_ON = 127
    # Value for turning off an LED.
    LED_OFF = 0

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

    # Program bank buttons (these are the channel select buttons)
    ID_BANK_SELECT1 = 34
    ID_BANK_SELECT2 = 35
    ID_BANK_SELECT3 = 36
    ID_BANK_SELECT4 = 37
    ID_BANK_SELECT5 = 38
    ID_BANK_SELECT6 = 39
    ID_BANK_SELECT7 = 40
    ID_BANK_SELECT8 = 41
    ID_BANK_SELECT9 = 42    # This is also the master/multi button

    # Array representation for the bank lights
    ARRAY_IDS_BANK_SELECT = [
        ID_BANK_SELECT1, ID_BANK_SELECT2, ID_BANK_SELECT3, ID_BANK_SELECT4, ID_BANK_SELECT5, ID_BANK_SELECT6,
        ID_BANK_SELECT7, ID_BANK_SELECT8, ID_BANK_SELECT9]

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

    # 4x4 pad
    ID_PAD_R1_C1 = 112
    ID_PAD_R1_C2 = 113
    ID_PAD_R1_C3 = 114
    ID_PAD_R1_C4 = 115

    ID_PAD_R2_C1 = 116
    ID_PAD_R2_C2 = 117
    ID_PAD_R2_C3 = 118
    ID_PAD_R2_C4 = 119

    ID_PAD_R3_C1 = 120
    ID_PAD_R3_C2 = 121
    ID_PAD_R3_C3 = 122
    ID_PAD_R3_C4 = 123

    ID_PAD_R4_C1 = 124
    ID_PAD_R4_C2 = 125
    ID_PAD_R4_C3 = 126
    ID_PAD_R4_C4 = 127

    # 4x4 lookup for the pad ids.
    MATRIX_IDS_PAD = [
        [ID_PAD_R1_C1, ID_PAD_R1_C2, ID_PAD_R1_C3, ID_PAD_R1_C4],
        [ID_PAD_R2_C1, ID_PAD_R2_C2, ID_PAD_R2_C3, ID_PAD_R2_C4],
        [ID_PAD_R3_C1, ID_PAD_R3_C2, ID_PAD_R3_C3, ID_PAD_R3_C4],
        [ID_PAD_R4_C1, ID_PAD_R4_C2, ID_PAD_R4_C3, ID_PAD_R4_C4],
    ]

    SET_COLOR_COMMAND = bytes([0x02, 0x00, 0x10])

    def __init__(self, send_fn=None):
        if send_fn is None:
            send_fn = send_to_device
        self._send_fn = send_fn

    @staticmethod
    def AsOnOffByte(is_on):
        """Converts a boolean to the corresponding on/off to use in the method calls of this class."""
        return ArturiaLights.LED_ON if is_on else ArturiaLights.LED_OFF

    @staticmethod
    def Zero4x4Matrix():
        return [[0]*4 for _ in range(4)]

    def SetPadLights(self, matrix_values):
        """ Set the pad lights given a matrix of color values to set the pad with.
        :param matrix_values: 4x4 array of arrays containing the LED color values.
        """
        # Note: Pad lights can be set to RGB colors, but this doesn't seem to be working.
        led_map = {}
        for r in range(4):
            for c in range(4):
                led_map[ArturiaLights.MATRIX_IDS_PAD[r][c]] = matrix_values[r][c]
        self.SetLights(led_map)

    def SetBankLights(self, array_values):
        """ Set the bank lights given an array of color values to set the bank lights with.

        :param array_values: a 9-element array containing the LED color values.
        """
        led_map = {k : v for k, v in zip(ArturiaLights.ARRAY_IDS_BANK_SELECT, array_values)}
        self.SetLights(led_map)

    def SetLights(self, led_mapping):
        """ Given a map of LED ids to color value, construct and send a command with all the led mapping. """
        data = bytes([])
        for led_id, led_value in led_mapping.items():
            data += bytes([led_id, led_value])
        self._send_fn(ArturiaLights.SET_COLOR_COMMAND + data)
