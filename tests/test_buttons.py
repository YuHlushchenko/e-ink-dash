"""
Test physical buttons without the display.

Press NEXT or PREV — the terminal prints which button was pressed.
Stop with Ctrl+C.
"""
import sys
import signal
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from gpiozero import Button
from config import BTN_NEXT_PIN, BTN_PREV_PIN, BTN_BOUNCE_TIME

btn_next = Button(BTN_NEXT_PIN, bounce_time=BTN_BOUNCE_TIME)
btn_prev = Button(BTN_PREV_PIN, bounce_time=BTN_BOUNCE_TIME)

btn_next.when_pressed = lambda: print('NEXT pressed')
btn_prev.when_pressed = lambda: print('PREV pressed')

print(f'Listening for buttons (NEXT=GPIO{BTN_NEXT_PIN}, PREV=GPIO{BTN_PREV_PIN}, bounce={BTN_BOUNCE_TIME}s)...')
print('Press Ctrl+C to stop.')

signal.pause()
