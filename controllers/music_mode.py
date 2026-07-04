import time

from actions.music_controller import (
    play_pause_music
)

HOLD_TIME = 1.0


def handle_music_mode(
    predicted_gesture,
    selected_music_action,
    music_action_start_time,
    music_cooldown,
    music_cooldown_start
):

    print("\n==============================")
    print("MUSIC MODE LOOP")
    print("Gesture:", predicted_gesture)
    print("Selected Action:", selected_music_action)
    print("Cooldown:", music_cooldown)
    print("==============================")

    # Mode-locking policy: MUSIC mode never exits via gesture,
    # only by quitting the program (Q). This is always False.
    exit_mode = False

    # ==========================
    # Cooldown
    # ==========================

    if music_cooldown:

        print("Cooldown Active")

        if (
            time.time()
            - music_cooldown_start
        ) > 2:

            music_cooldown = False

            print(
                "Cooldown Finished"
            )

    else:

        # ==========================
        # OPEN PALM
        # ==========================

        if predicted_gesture == "OPEN_PALM":

            print(
                "OPEN PALM DETECTED"
            )

            if (
                selected_music_action
                != "PLAY_PAUSE"
            ):

                print(
                    "Starting Play/Pause Timer"
                )

                selected_music_action = (
                    "PLAY_PAUSE"
                )

                music_action_start_time = (
                    time.time()
                )

            else:

                elapsed = (
                    time.time()
                    - music_action_start_time
                )

                print(
                    f"Play Hold = {elapsed:.2f}s"
                )

                if elapsed >= HOLD_TIME:

                    print(
                        "PLAY / PAUSE TRIGGERED"
                    )

                    play_pause_music()

                    selected_music_action = None
                    music_action_start_time = None

                    music_cooldown = True
                    music_cooldown_start = (
                        time.time()
                    )

        # ==========================
        # OTHER GESTURES
        # ==========================

        else:

            print(
                "OTHER GESTURE DETECTED"
            )

            selected_music_action = None
            music_action_start_time = None

    return (
        selected_music_action,
        music_action_start_time,
        music_cooldown,
        music_cooldown_start,
        exit_mode
    )