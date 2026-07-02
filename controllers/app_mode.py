import time

from actions.app_controller import (
    open_chrome,
    open_powerpoint,
    open_word,
    open_vscode
)

HOLD_TIME = 1.0


def handle_app_mode(
    finger_count,
    selected_app,
    selection_start_time
):

    current_app = None

    if finger_count == 1:
        current_app = "Chrome"

    elif finger_count == 2:
        current_app = "PowerPoint"

    elif finger_count == 3:
        current_app = "Word"

    elif finger_count == 4:
        current_app = "VS Code"

    launched = False

    if current_app:

        if selected_app != current_app:

            selected_app = current_app
            selection_start_time = time.time()

        else:

            elapsed = (
                time.time()
                - selection_start_time
            )

            if elapsed >= HOLD_TIME:

                if selected_app == "Chrome":
                    open_chrome()

                elif selected_app == "PowerPoint":
                    open_powerpoint()

                elif selected_app == "Word":
                    open_word()

                elif selected_app == "VS Code":
                    open_vscode()

                launched = True

    return (
        selected_app,
        selection_start_time,
        launched
    )