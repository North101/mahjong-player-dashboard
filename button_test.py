import io
import os
import select
import struct
from typing import Callable, Union

import badger2040
from machine import Pin

msg_length = struct.Struct('>I')


def create_msg(msg: bytes):
  return msg_length.pack(len(msg)) + msg


def write_msg(writer: io.BufferedWriter, msg: bytes):
  writer.write(create_msg(msg))
  writer.flush()


def read_msg(reader: io.BufferedReader):
  data = readall(reader, msg_length.size)
  if not data:
    return None
  length = msg_length.unpack(data)[0]
  return readall(reader, length)


def readall(reader: io.BufferedReader, length: int):
  data = bytearray()
  while len(data) < length:
    packet = reader.read(length - len(data))
    if not packet:
      return None
    data.extend(packet)
  return data


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


display = badger2040.Badger2040()
display.update_speed(badger2040.UPDATE_TURBO)
display.pen(15)
display.clear()
display.update()


def update_display(button: Button):
  if button.id == badger2040.BUTTON_A:
    message = 'BUTTON_A'
  elif button.id == badger2040.BUTTON_B:
    message = 'BUTTON_B'
  elif button.id == badger2040.BUTTON_C:
    message = 'BUTTON_C'
  elif button.id == badger2040.BUTTON_UP:
    message = 'BUTTON_UP'
  elif button.id == badger2040.BUTTON_DOWN:
    message = 'BUTTON_DOWN'
  elif button.id == badger2040.BUTTON_USER:
    message = 'BUTTON_USER'
  else:
    message = 'UNKNOWN'

  display.pen(15)
  display.clear()
  display.pen(0)
  display.thickness(4)
  display.text(message, 6, 60, 1.4)
  for _ in range(2):
    display.update()


button_handler = ButtonHandler()
poll = select.poll()
poll.register(button_handler)
for (fd, event) in poll.poll():
  if fd == button_handler.fileno():
    update_display(button_handler.read_button())
