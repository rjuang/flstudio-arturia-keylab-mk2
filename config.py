# User-settable settings to alter behavior of keyboard

# Number representing the last change date
CHANGE_DATE = 2021_07_16_2347

# Set to True to allow drum pads to light up as a metronome indicator.
ENABLE_PAD_METRONOME_LIGHTS = True

# Set to True to allow transport lights to light up as a metronome indicator.
ENABLE_TRANSPORTS_METRONOME_LIGHTS = True

# Set to True to only allow visual metronome lights when audible metronome in FL Studio is enabled.
# Set to False to always enable visual metronome lights when playing/recording.
METRONOME_LIGHTS_ONLY_WHEN_METRONOME_ENABLED = False

# Set to True to enable piano roll to be focused on during playback/record. This is needed for punch buttons to work.
ENABLE_PIANO_ROLL_FOCUS_DURING_RECORD_AND_PLAYBACK = True

# Configure the port number that midi notes are forwarded to for plugins.
PLUGIN_FORWARDING_MIDI_IN_PORT = 10

# Set to True to put display text hints in all caps.
HINT_DISPLAY_ALL_CAPS = False

# Set to True to enable color bank lights. On Essential keyboards, the pad colors are set to the active channel color.
ENABLE_COLORIZE_BANK_LIGHTS = True

# If True, then sliders initially control plugin. If False, sliders initially control mixer tracks.
SLIDERS_FIRST_CONTROL_PLUGINS = False

# If True, the sliders are initially ignored until they cross the initial value in the mixer. For example, if mixer
# for track 1 is set to 100% and mixer is at 50%, then mixer sliders won't do anything until they cross or match the
# value of the mixer.
ENABLE_MIXER_SLIDERS_PICKUP_MODE = False
