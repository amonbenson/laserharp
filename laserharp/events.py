class EventEmitter:
    def __init__(self):
        self._events: dict[str, list[callable]] = {}

    def on(self, event: str, callback: callable):
        if event not in self._events:
            self._events[event] = []

        self._events[event].append(callback)

    def off(self, event: str, callback: callable):
        if event not in self._events:
            return

        self._events[event].remove(callback)

    def emit(self, event: str, *args, **kwargs):
        if event not in self._events:
            return

        for callback in self._events[event]:
            callback(*args, **kwargs)
