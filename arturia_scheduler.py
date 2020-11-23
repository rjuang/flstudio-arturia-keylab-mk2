import _heapq
import time


class Scheduler:
    """ The purpose of this class is to provide a way for tasks to be scheduled in a thread-safe manner.

    FL Studio's midi script does not allow usage of the threading library in Python. As such, we need to implement
    a scheduler that runs on the OnIdle loop of the midi script. This allows one to schedule future tasks without
    needing to worry about additional boiler-plate code. The only requirement is that this class's Refresh method
    must be hooked up to midiscript's the OnIdle event.
    """
    def __init__(self):
        self._tasks_pq = []

    def ScheduleTask(self, task, delay=0):
        time_ms = time.monotonic() * 1000
        entry = (time_ms + delay, task)
        _heapq.heappush(self._tasks_pq, entry)
        return entry

    def CancelTask(self, entry):
        try:
            self._tasks_pq.remove(entry)
            return True
        except ValueError:
            # Entry was already removed and executed.
            return False

    def Idle(self):
        time_ms = time.monotonic() * 1000
        while self._tasks_pq:
            entry = _heapq.heappop(self._tasks_pq)
            if entry[0] > time_ms:
                # Entry delay condition not met. Put back on queue and wait until next refresh cycle.
                _heapq.heappush(self._tasks_pq, entry)
                return
            task = entry[1]
            task()
