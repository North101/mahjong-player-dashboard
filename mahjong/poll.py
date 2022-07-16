import select
from ast import Tuple
from typing import Callable, Mapping

from mahjong.packets import *


class FileDescriptorLike:
  def fileno(self) -> int:
    raise NotImplementedError()


class Poll:
  lookup: Mapping[int, Tuple[FileDescriptorLike, Callable]] = {}

  def __init__(self):
    self._poll = select.poll()

  def register(self, fd: FileDescriptorLike, eventmask: int, callback: Callable):
    self._poll.register(fd, eventmask)
    self.lookup[fd.fileno()] = (fd, callback)

  def unregister(self, fd: FileDescriptorLike):
    self._poll.unregister(fd)
    del self.lookup[fd.fileno()]

  def poll(self):
    for (fileno, event) in self._poll.poll():
      if fileno not in self.lookup:
        continue

      fd, callback = self.lookup[fileno]
      callback(fd, event)
