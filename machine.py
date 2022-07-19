from typing import Callable, Union


class Pin:
  IN = 0
  OUT = 0
  OPEN_DRAIN = 0

  PULL_UP = 0
  PULL_DOWN = 0
  PULL_HOLD = 0

  IRQ_FALLING = 0
  IRQ_RISING = 0
  IRQ_LOW_LEVEL = 0
  IRQ_HIGH_LEVEL = 0

  def __init__(self, id: int, mode: int = - 1, pull: int = - 1, *,
               value=Union[int, None], drive: int = 0, alt: int = - 1):
    pass

  def irq(self, handler: Union[Callable[[int], None], None] = None, trigger=int, *, priority=1, wake=None, hard=False):
    pass
