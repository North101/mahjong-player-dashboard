import select
from ast import Tuple
from typing import Callable, Mapping

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
  lookup: Mapping[int, EventCallback] = {}

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
      if not event_callback: continue
      event_callback(event)
