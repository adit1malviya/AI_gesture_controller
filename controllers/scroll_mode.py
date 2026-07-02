from actions.app_controller import (
    scroll_up,
    scroll_down
)

SCROLL_THRESHOLD = 20


def handle_scroll_mode(
    current_y,
    previous_y
):

    if previous_y is None:
        return current_y

    difference = (
        current_y - previous_y
    )

    # Hand moved down
    if difference > SCROLL_THRESHOLD:

        print("SCROLL DOWN")

        scroll_down()

    # Hand moved up
    elif difference < -SCROLL_THRESHOLD:

        print("SCROLL UP")

        scroll_up()

    return current_y