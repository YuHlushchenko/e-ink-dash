from gpiozero import Button
from renderer.base import Renderer
from screens.screen1 import Screen1
from screens.screen2 import Screen2
from config import BTN_NEXT_PIN, BTN_PREV_PIN


def main():
    renderer = Renderer()
    renderer.init()
    renderer.clear()

    screens = [
        Screen1(renderer),
        Screen2(renderer),
    ]

    current = 0

    def show_current():
        image = screens[current].render()
        renderer.display(image)

    def next_screen():
        nonlocal current
        current = (current + 1) % len(screens)
        show_current()

    def prev_screen():
        nonlocal current
        current = (current - 1) % len(screens)
        show_current()

    btn_next = Button(BTN_NEXT_PIN)
    btn_prev = Button(BTN_PREV_PIN)
    btn_next.when_pressed = next_screen
    btn_prev.when_pressed = prev_screen

    show_current()
    renderer.sleep()

    from signal import pause
    pause()


if __name__ == '__main__':
    main()
