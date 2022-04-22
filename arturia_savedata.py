import mixer

class SaveData:
    """ Provides a way to bundle data into an FL Studio project output file.

    SaveData takes advantage of the fact that pattern/mixer names in FL Studio do not have any character limitation.
    As such, we can just encode a very long string for all the data we want to save into the name of a new pattern
    track.
    """
    def __init__(self):
        self._datastore = {}
        self._last_state = ''

    def _get_pattern_name(self):
        return 'DO NOT EDIT:SAVEDATA|'

    def _is_data_stale(self):
        return self._last_state != self._find_data()

    def _find_data(self):
        prefix = self._get_pattern_name()
        name = mixer.getTrackName(mixer.trackCount() - 1)
        if name.startswith(prefix):
            line = name[len(prefix):]
            self._last_state = line
            return line
        return ''

    def _set_data(self, line):
        mixer.setTrackName(mixer.trackCount() - 1, self._get_pattern_name() + line)

    def _encode_as_str(self):
        items = []
        for key, int_values in self._datastore.items():
            items.append('%s:%s' % (str(key), '|'.join([str(i) for i in int_values])))
        return ','.join(items)

    def _decode_from_str(self, line):
        result = {}
        for token in line.split(','):
            values = token.split(':', 1)
            if not values:
                continue
            key = values[0]
            data = values[-1]
            if not key or not data:
                continue
            values = [int(v) for v in data.split('|')]
            result[key] = values
        return result

    def Load(self):
        # Find first track with given prefix name
        if not self._is_data_stale():
            return
        print('Loading drum pad patterns from project')
        line = self._find_data()
        self._datastore = self._decode_from_str(line)

    def Commit(self):
        self._set_data(self._encode_as_str())

    def Get(self, key):
        if key not in self._datastore:
            self._datastore[key] = []
        return self._datastore[key]

    def Put(self, key, int_values):
        self._datastore[key] = int_values

    def ContainsNonEmpty(self, key):
        return key in self._datastore and self._datastore[key]
