"""Module to support tracking and selecting playlist tracks."""
import channels
import patterns
import playlist

_current_playlist_track = 1


def current_playlist_track():
    """Returns the current playlist track."""
    global _current_playlist_track
    return _current_playlist_track


def _deselect_all_playlist_track():
    for i in range(1, playlist.trackCount()):
        track_name = playlist.getTrackName(i)
        if track_name.startswith('* '):
            playlist.setTrackName(i, track_name[2:])


def strip_pattern_name(name):
    if name.startswith('* '):
        return name[2:]
    return name


def _select_pattern_named(name):
    for i in range(1, patterns.patternCount() + 1):
        if strip_pattern_name(patterns.getPatternName(i)) == name:
            patterns.jumpToPattern(i)
            return
    # No pattern found
    patterns.deselectAll()


def set_playlist_track(track):
    global _current_playlist_track
    _current_playlist_track = track

    name = playlist.getTrackName(track)
    if name.startswith('* '):
        return

    _deselect_all_playlist_track()
    _select_pattern_named(name)
    playlist.setTrackName(track, '* ' + name)


def _all_pattern_names():
    return (strip_pattern_name(patterns.getPatternName(i)) for i in range(1, patterns.patternCount() + 1))


def next_pattern_name():
    """Returns the next suggested pattern name."""
    pattern_names = _all_pattern_names()
    # If there are N patterns, then at most, N+1 instruments
    selected = channels.selectedChannel()
    name = strip_pattern_name(channels.getChannelName(selected))
    if name not in pattern_names:
        return name

    for i in range(1, patterns.patternCount() + 1):
        suggested = '%s [%d]' % (name, i)
        if suggested not in pattern_names:
            return suggested
    return '%s [%d]' % (name, patterns.patternCount() + 1)


def _select_playlist_track_named(name):
    base = name.split(' [')[0]
    for i in range(1, playlist.trackCount()):
        track_name = get_playlist_track_name(i)
        if track_name == base:
            set_playlist_track(i)
            return


def _select_channel_from_name(name):
    base = name.split(' [')[0]
    for i in range(channels.channelCount()):
        if base == channels.getChannelName(i):
            channels.deselectAll()
            channels.selectChannel(i, 1)
            return True
    return False


def get_playlist_track_name(track):
    """Returns the playlist track name."""
    return strip_pattern_name(playlist.getTrackName(track))


def select_playlist_track_from_pattern(pattern_index):
    """Select the specified pattern"""
    name = get_playlist_track_name(pattern_index)
    _select_channel_from_name(name)
    _select_playlist_track_named(name)
    patterns.jumpToPattern(pattern_index)
