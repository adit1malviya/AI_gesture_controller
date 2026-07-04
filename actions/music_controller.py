import pyautogui
import win32gui


def get_active_window_title():

    try:

        window = win32gui.GetForegroundWindow()

        return win32gui.GetWindowText(window)

    except Exception:

        return ""


def play_pause_music():
    pyautogui.press("playpause")


def next_track():

    title = get_active_window_title().lower()

    if "youtube" in title:

        print("YouTube detected -> Seek forward 5s")

        pyautogui.press("right")

    else:

        print("Music app detected -> Next track")

        pyautogui.press("nexttrack")


def previous_track():

    title = get_active_window_title().lower()

    if "youtube" in title:

        print("YouTube detected -> Seek backward 5s")

        pyautogui.press("left")

    else:

        print("Music app detected -> Previous track")

        pyautogui.press("prevtrack")


def volume_up():
    pyautogui.press("volumeup")


def volume_down():
    pyautogui.press("volumedown")