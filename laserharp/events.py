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


class Ref(EventEmitter):
    def __init__(self, value):
        super().__init__()
        self._value = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if self._value == value:
            return

        self._value = value
        self.emit("change", value)

    def update(self, value):
        if not isinstance(self._value, dict):
            raise TypeError("Ref must contain a dictionary")
        if not isinstance(value, dict):
            raise TypeError("Value must be a dictionary")

        # check if any key has changed
        changed = False
        for key in value:
            if self._value.get(key) != value[key]:
                changed = True
                break
        if not changed:
            return

        # update the value
        self._value.update(value)
        self.emit("change", self._value)

    def watch(self, callback: callable, immediate=False):
        self.on("change", callback)

        if immediate:
            callback(self._value)
