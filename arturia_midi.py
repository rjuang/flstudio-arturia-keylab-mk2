import debug
import device

# Status command to use when sending commands between scripts
INTER_SCRIPT_STATUS_BYTE = 0x00
INTER_SCRIPT_DATA1_BTN_DOWN_CMD = 0x01     # Data2 contains the id of the button
INTER_SCRIPT_DATA1_BTN_UP_CMD = 0x02       # Data2 contains the id of the button

INTER_SCRIPT_DATA1_BEGIN_PAYLOAD_CMD = 0xFE
INTER_SCRIPT_DATA1_END_PAYLOAD_CMD = 0xFF
PAYLOAD_STATUS_BYTE = 0x01
PLUGIN_PORT_NUM = 10
SYSEX_HEADER = [0xF0, 0x00, 0x20, 0x6B, 0x7F, 0x42]
SYSEX_FOOTER = [0xF7]


class MidiEventDispatcher:
    """ Dispatches a MIDI event after feeding it through a transform function.

    MIDI event dispatcher transforms the MIDI event into a value through a transform function provided at construction
    time. This value is then used as a key into a lookup table that provides a dispatcher and filter function. If the
    filter function returns true, then the event is sent to the dispatcher function.
    """
    def __init__(self, transform_fn):
        self._transform_fn = transform_fn
        # Table contains a mapping of status code -> (callback_fn, filter_fn)
        self._dispatch_map = {}

    def SetHandler(self, key, callback_fn, filter_fn=None):
        """ Associate a handler function and optional filter predicate function to a key.

        If the transform of the midi event matches the key, then the event is dispatched to the callback function
        given that the filter predicate function also returns true.

        :param key: the result value of transform_fn(event) to match against.
        :param callback_fn: function that is called with the event in the event the transformed event matches.
        :param filter_fn: function that takes an event and returns true if the event should be dispatched. If false
        is returned, then the event is dropped and never passed to callback_fn. Not specifying means that callback_fn
        is always called if transform_fn matches the key.
        """
        def _default_true_fn(_): return True
        if filter_fn is None:
            filter_fn = _default_true_fn
        self._dispatch_map[key] = (callback_fn, filter_fn)
        return self

    def SetHandlerForKeys(self, keys, callback_fn, filter_fn=None):
        """ Associate the same handler for a group of keys. See SetHandler for more details. """
        for k in keys:
            self.SetHandler(k, callback_fn, filter_fn=filter_fn)
        return self

    def Dispatch(self, event):
        """ Dispatches a midi event to the appropriate listener.

        :param event:  the event to dispatch.
        """
        key = self._transform_fn(event)
        processed = False
        if key in self._dispatch_map:
            callback_fn, filter_fn = self._dispatch_map[key]
            if filter_fn(event):
                callback_fn(event)
                processed = True
            else:
                debug.log("DISPATCHER", "Event dropped by filter.", event=event)
                processed = True
        else:
            debug.log("DISPATCHER", "No handler found.", event=event)

        return processed


def send_to_device(data):
    """Sends a data payload to Arturia device. """
    # debug.log('CMD', 'Sending payload: ' + str(data))
    # Reference regarding SysEx code : # https://forum.arturia.com/index.php?topic=90496.0
    device.midiOutSysex(bytes(SYSEX_HEADER) + bytes(data) + bytes(SYSEX_FOOTER))


def dispatch_message_to_other_scripts(status, data1, data2, payload=None):
    """ Sends midi commands to other scripts scripts. """
    for i in range(device.dispatchReceiverCount()):
        msg = status + (data1 << 8) + (data2 << 16)
        if payload is None:
            device.dispatch(i, msg)
        else:
            msg = INTER_SCRIPT_DATA1_BEGIN_PAYLOAD_CMD
            msg += (INTER_SCRIPT_DATA1_BEGIN_PAYLOAD_CMD << 8)
            device.dispatch(i, msg)

            # Send payload
            for j in range(0, len(payload), 2):
                msg = PAYLOAD_STATUS_BYTE + (payload[j] << 8)
                if j + 1 < len(payload):
                   msg += (payload[j + 1] << 16)
                device.dispatch(i, msg)

            msg = INTER_SCRIPT_STATUS_BYTE
            msg += (INTER_SCRIPT_DATA1_END_PAYLOAD_CMD << 8)
            device.dispatch(i, msg)

