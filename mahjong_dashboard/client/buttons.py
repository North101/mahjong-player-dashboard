import os
import random
import struct
from typing import Callable

import badger2040
from machine import Pin
from mahjong_dashboard.packets import create_msg, read_msg

button_struct = struct.Struct('B')


class Button:
  def __init__(self, id: int, invert: bool = True):
    self.id = id
    self.pin = Pin(id, Pin.IN, Pin.PULL_UP if invert else Pin.PULL_DOWN)
    self.msg = create_msg(button_struct.pack(id))

  def irq(self, handler: Callable[[int], None]):
    self.pin.irq(trigger=Pin.IRQ_RISING, handler=handler)

  def value(self):
    return self.pin.value()


class ButtonHandler:
  buttons = {
      badger2040.BUTTON_A: Button(badger2040.BUTTON_A, invert=False),
      badger2040.BUTTON_B: Button(badger2040.BUTTON_B, invert=False),
      badger2040.BUTTON_C: Button(badger2040.BUTTON_C, invert=False),
      badger2040.BUTTON_UP: Button(badger2040.BUTTON_UP, invert=False),
      badger2040.BUTTON_DOWN: Button(badger2040.BUTTON_DOWN, invert=False),
      badger2040.BUTTON_USER: Button(badger2040.BUTTON_USER),
  }

  def __init__(self):
    r, w = os.pipe()
    self.reader = os.fdopen(r, 'rb')
    self.writer = os.fdopen(w, 'wb')

    for button in self.buttons.values():
      button.irq(self.on_button)

  def fileno(self):
    return self.reader.fileno()

  def on_button(self, pin: int):
    button = self.buttons[pin]
    self.writer.write(button.msg)
    self.writer.flush()

  def read_button(self):
    pin = button_struct.unpack(read_msg(self.reader))[0]
    return self.buttons[pin]

  def write_random_button(self, *_):
    self.on_button(random.choice(list(self.buttons.keys())))
