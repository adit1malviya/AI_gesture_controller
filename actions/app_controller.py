import subprocess
import pyautogui


def scroll_up():
    pyautogui.scroll(300)


def scroll_down():
    pyautogui.scroll(-300)


def open_chrome():
    subprocess.Popen(
        r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    )


def open_powerpoint():
    subprocess.Popen(
        r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE"
    )


def open_word():
    subprocess.Popen(
        r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE"
    )


def open_vscode():
    subprocess.Popen("code")