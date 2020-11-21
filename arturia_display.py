import time

from arturia_midi import send_to_device


class ArturiaDisplay:
    """ Manages scrolling display of two lines so that long strings can be scrolled on each line. """
    def __init__(self):
        # Holds the text to display on first line. May exceed the 16-char display limit.
        self._line1 = ' '
        # Holds the text to display on second line. May exceed the 16-char display limit.
        self._line2 = ' '

        # Holds ephemeral text that will expire after the expiration timestamp. These lines will display if the
        # the expiration timestamp is > current timestamp.
        self._ephemeral_line1 = ' '
        self._ephemeral_line2 = ' '
        self._expiration_time_ms = 0

        # Holds the starting offset of where the line1 text should start.
        self._line1_display_offset = 0
        # Holds the starting offset of where the line2 text should start.
        self._line2_display_offset = 0
        # Last timestamp in milliseconds in which the text was updated.
        self._last_update_ms = 0
        # Minimum interval before text is scrolled
        self._scroll_interval_ms = 500
        # How many characters to allow last char to scroll before starting over.
        self._end_padding = 8
        # Track what's currently being displayed
        self._last_payload = bytes()

    def _get_line1_bytes(self):
        # Get up to 16-bytes the exact chars to display for line 1.
        start_pos = self._line1_display_offset
        end_pos = start_pos + 16
        line_src = self._line1
        if self._expiration_time_ms > self.time_ms():
            line_src = self._ephemeral_line1
        return bytearray(line_src[start_pos:end_pos], 'ascii')

    def _get_line2_bytes(self):
        # Get up to 16-bytes the exact chars to display for line 2.
        start_pos = self._line2_display_offset
        end_pos = start_pos + 16
        line_src = self._line2
        if self._expiration_time_ms > self.time_ms():
            line_src = self._ephemeral_line2
        return bytearray(line_src[start_pos:end_pos], 'ascii')

    def _get_new_offset(self, start_pos, line_src):
        end_pos = start_pos + 16
        if end_pos >= len(line_src) + self._end_padding or len(line_src) <= 16:
            return 0
        else:
            return start_pos + 1

    def _update_scroll_pos(self):
        current_time_ms = self.time_ms()
        if current_time_ms >= self._scroll_interval_ms + self._last_update_ms:
            self._line1_display_offset = self._get_new_offset(self._line1_display_offset, self._line1)
            self._line2_display_offset = self._get_new_offset(self._line2_display_offset, self._line2)
            self._last_update_ms = current_time_ms

    @staticmethod
    def time_ms():
        # Get the current timestamp in milliseconds
        return time.monotonic() * 1000

    _ABBREVIATION_MAP = {
        'VOLUME': 'VOL',
        'ENVELOPE': 'ENV',
        'FILTER': 'FLT',
        'ATTACK': 'ATK',
        'RESONANCE': 'RES',
        'PARAMETER': 'PARAM',
        'MASTER': 'MSTR',
        'SIZE': 'SZ',
    }
    @staticmethod
    def abbreviate(line):
        if len(line) <= 16:
            return line
        words = line.split(' ')
        shortened_words = []
        for w in words:
            if not w:
                continue
            if w in ArturiaDisplay._ABBREVIATION_MAP:
                w = ArturiaDisplay._ABBREVIATION_MAP[w]
            shortened_words.append(w)
        return ' '.join(shortened_words)

    def _refresh_display(self):
        # Internally called to refresh the display now.
        data = bytes([0x04, 0x00, 0x60])
        data += bytes([0x01]) + self._get_line1_bytes() + bytes([0x00])
        data += bytes([0x02]) + self._get_line2_bytes() + bytes([0x00])
        data += bytes([0x7F])

        self._update_scroll_pos()
        if self._last_payload != data:
            send_to_device(data)
            self._last_payload = data

    def ResetScroll(self):
        self._line1_display_offset = 0
        self._line2_display_offset = 0

    def SetLines(self, line1=None, line2=None, expires=None):
        """ Update lines on the display, or leave alone if not provided.

        :param line1:    first line to update display with or None to leave as is.
        :param line2:    second line to update display with or None to leave as is.
        :param expires:  number of milliseconds that the line persists before expiring. Note that when an expiration
            interval is provided, lines are interpreted as a blank line if not provided.
        """
        if expires is None:
            if line1 is not None:
                self._line1 = line1
            if line2 is not None:
                self._line2 = line2
        else:
            self._expiration_time_ms = self.time_ms() + expires
            if line1 is not None:
                self._ephemeral_line1 = line1
            if line2 is not None:
                self._ephemeral_line2 = line2

        self._refresh_display()
        return self

    def Refresh(self):
        """ Called to refresh the display, possibly with updated text. """
        if self.time_ms() - self._last_update_ms >= self._scroll_interval_ms:
            self._refresh_display()
        return self