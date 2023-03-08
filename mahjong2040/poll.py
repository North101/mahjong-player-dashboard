import select
from typing import Any, Callable


class EventCallback:
  def __init__(self, fd: Any, callback: Callable[[Any, int], None]):
    self.fd = fd
    self.callback = callback

  def __call__(self, event: int):
    self.callback(self.fd, event)


class Poll:
  lookup: dict[int, EventCallback] = {}

  def __init__(self):
    self._poll = select.poll()

  def register(self, fd: Any, eventmask: int, callback: Callable[[Any, int], None]):
    self._poll.register(fd, eventmask)
    self.lookup[id(fd)] = EventCallback(fd, callback)

  def unregister(self, fd: Any):
    self._poll.unregister(fd)
    del self.lookup[id(fd)]

  def poll(self):
    for (fd, event) in self._poll.ipoll(0):
      event_callback = self.lookup.get(id(fd))
      if not event_callback:
        continue
      event_callback(event)

  def close(self):
    for event_callback in list(self.lookup.values()):
      self.unregister(event_callback.fd)
