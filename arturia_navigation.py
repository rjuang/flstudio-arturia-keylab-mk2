class NavigationMode:
    def __init__(self, paged_display, display_ms=2000):
        self._paged_display = paged_display
        self._display_ms = 2000
        self._modes = []
        self._active_index = 0

    def AddMode(self, name, update_fn, knob_press_fn, line_fn):
        self._modes.append((name, update_fn, knob_press_fn, line_fn))
        self._paged_display.SetPageLinesProvider(name, line1=lambda: name, line2=line_fn)
        return self

    def PreviousMode(self):
        self._active_index -= 1
        if self._active_index < 0:
            self._active_index = len(self._modes) - 1
        self._refresh()

    def NextMode(self):
        self._active_index += 1
        if self._active_index >= len(self._modes):
            self._active_index = 0
        self._refresh()

    def GetMode(self):
        return self._modes[self._active_index][0]

    def UpdateValue(self, delta):
        if self._active_index >= len(self._modes):
            return
        self._modes[self._active_index][1](delta)
        self._refresh()

    def NotifyKnobPressed(self):
        if self._active_index >= len(self._modes):
            return
        self._modes[self._active_index][2]()
        self._refresh()

    def _refresh(self):
        self._paged_display.SetActivePage(self._modes[self._active_index][0], expires=self._display_ms)