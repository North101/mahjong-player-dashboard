import select
from typing import Callable

from mahjong.packets import *


class FileDescriptorLike:
  def fileno(self) -> int:
    raise NotImplementedError()


class EventCallback:
  def __init__(self, fd: FileDescriptorLike, callback: Callable):
    self.fd = fd
    self.callback = callback

  def __call__(self, event: int):
    self.callback(self.fd, event)


class Poll:
  lookup: Dict[int, EventCallback] = {}

  def __init__(self):
    self._poll = select.poll()

  def register(self, fd: FileDescriptorLike, eventmask: int, callback: Callable):
    self._poll.register(fd, eventmask)
    self.lookup[fd.fileno()] = EventCallback(fd, callback)

  def unregister(self, fd: FileDescriptorLike):
    self._poll.unregister(fd)
    del self.lookup[fd.fileno()]

  def poll(self):
    for (fileno, event) in self._poll.poll():
      event_callback = self.lookup.get(fileno)
      if not event_callback:
        continue
      event_callback(event)

  def close(self):
    for event_callback in list(self.lookup.values()):
      self.unregister(event_callback.fd)
