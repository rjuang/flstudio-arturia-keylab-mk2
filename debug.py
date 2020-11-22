# Enable to log messages out to console.
DEBUG = False

def log(tag, message, event=None):
    """Log out messages to the script console if global DEBUG variable is True."""
    if DEBUG:
        event_str = _event_as_string(event) if event is not None else '_' * 63
        print('%63s | [%s] %s' % (event_str, tag, message))


def _event_as_string(event):
    """Convert a midi event packet to a string representation."""
    return '[id, status, cnum, cval, d1, d2] = %3d, %3d, %3d, %3d, %3d, %3d' % (
        event.midiId, event.status, event.controlNum, event.controlVal, event.data1, event.data2)