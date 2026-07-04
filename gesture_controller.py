import cv2
import mediapipe as mp
import joblib
import time

from collections import deque

from controllers.app_mode import (
    handle_app_mode
)

from controllers.music_mode import (
    handle_music_mode
)

from actions.app_controller import (
    scroll_up,
    scroll_down,
    close_app
)

from actions.music_controller import (
    next_track,
    previous_track,
    volume_up,
    volume_down
)

# ==========================
# Load Model
# ==========================

model = joblib.load("gesture_model.pkl")

# ==========================
# MediaPipe Setup
# ==========================

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    max_num_hands=2,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

cap = cv2.VideoCapture(0)

# ==========================
# Finger Tips
# ==========================

tip_ids = [8, 12, 16, 20]

# ==========================
# Gesture Smoothing (for ML-based mode entry)
# ==========================

GESTURE_BUFFER_SIZE = 5
gesture_buffer = deque(maxlen=GESTURE_BUFFER_SIZE)


def get_stable_gesture(buffer, new_gesture):

    buffer.append(new_gesture)

    if len(buffer) < buffer.maxlen:
        return None

    if all(g == buffer[0] for g in buffer):
        return buffer[0]

    return None


# ==========================
# Closed-Fist Smoothing (for CLOSE APP action, APP mode)
# ==========================

CLOSED_FIST_HOLD_FRAMES = 8
closed_fist_buffer = deque(maxlen=CLOSED_FIST_HOLD_FRAMES)

# ==========================
# Two-Hand State Helper
# ==========================
# Shared by scrolling (APP mode) and track switching (MUSIC mode).


def get_two_hand_state(hand_finger_counts):

    if len(hand_finger_counts) != 2:
        return None

    open_count = sum(
        1 for c in hand_finger_counts if c >= 4
    )

    closed_count = sum(
        1 for c in hand_finger_counts if c == 0
    )

    if open_count == 2:
        return "BOTH_OPEN"

    if closed_count == 2:
        return "BOTH_CLOSED"

    if open_count == 1 and closed_count == 1:
        return "ONE_OPEN_ONE_CLOSED"

    return None


# ==========================
# Two-Hand Scroll Settings (APP mode)
# ==========================

SCROLL_COOLDOWN = 0.15
last_scroll_time = 0

# ==========================
# Two-Hand Track Settings (MUSIC mode)
# ==========================

TRACK_HOLD_FRAMES = 6
TRACK_COOLDOWN = 1.2

track_state_buffer = deque(maxlen=TRACK_HOLD_FRAMES)
last_track_time = 0

# ==========================
# Single-Hand Volume Settings (MUSIC mode)
# ==========================

VOLUME_HOLD_FRAMES = 4
VOLUME_COOLDOWN = 0.4

volume_finger_buffer = deque(maxlen=VOLUME_HOLD_FRAMES)
last_volume_time = 0

# ==========================
# Single-Hand Close Window Settings (MUSIC mode)
# ==========================
# 3 fingers (single hand), held steady, closes the currently
# focused window (YouTube tab / music app) via Alt+F4.
# MUSIC mode itself stays locked afterward.

MUSIC_CLOSE_HOLD_FRAMES = 8
MUSIC_CLOSE_COOLDOWN = 1.5

music_close_buffer = deque(maxlen=MUSIC_CLOSE_HOLD_FRAMES)
last_music_close_time = 0

# ==========================
# State Variables
# ==========================

mode = "NONE"
mode_locked = False

gesture = "NONE"

# APP MODE

selected_app = None
selection_start_time = None

# MUSIC MODE

selected_music_action = None
music_action_start_time = None

music_cooldown = False
music_cooldown_start = None

scroll_mode = False

# ==========================
# Main Loop
# ==========================

while True:

    success, frame = cap.read()

    if not success:
        break

    frame = cv2.flip(frame, 1)

    rgb_frame = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )

    results = hands.process(rgb_frame)

    finger_count = 0

    predicted_gesture = "NONE"
    stable_gesture = None

    hand_detected = False
    hand_finger_counts = []

    # ==========================
    # Hand Detection
    # ==========================

    if results.multi_hand_landmarks:

        hand_detected = True

        for idx, hand_landmarks in enumerate(
            results.multi_hand_landmarks
        ):

            mp_draw.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS
            )

            landmarks = []

            h, w, c = frame.shape

            for lm in hand_landmarks.landmark:

                x = int(lm.x * w)
                y = int(lm.y * h)

                landmarks.append((x, y))

            # ==========================
            # Per-Hand Finger Count
            # ==========================

            hand_fc = 0

            for tip in tip_ids:

                if landmarks[tip][1] < landmarks[tip - 2][1]:

                    hand_fc += 1

            hand_finger_counts.append(hand_fc)

            # ==========================
            # Primary Hand Only:
            # Finger count for app selection, ML gesture
            # prediction, and mode selection stay exactly
            # as before.
            # ==========================

            if idx == 0:

                finger_count = hand_fc

                features = []

                for lm in hand_landmarks.landmark:

                    features.extend([
                        lm.x,
                        lm.y,
                        lm.z
                    ])

                predicted_gesture = model.predict([features])[0]
                print("Gesture:", predicted_gesture)
                gesture = predicted_gesture

                stable_gesture = get_stable_gesture(
                    gesture_buffer,
                    predicted_gesture
                )

                # ==========================
                # Mode Selection
                # ==========================
                # Only two modes exist: APP and MUSIC. Once
                # mode_locked is True, this block never runs
                # again for the rest of the program's lifetime.

                if not mode_locked:

                    if stable_gesture == "THUMBS_DOWN":

                        mode = "APP"
                        mode_locked = True

                        print("APP MODE")

                    elif stable_gesture == "THUMBS_UP":

                        mode = "MUSIC"
                        mode_locked = True

                        print("MUSIC MODE")

    else:

        gesture_buffer.clear()
        closed_fist_buffer.clear()
        track_state_buffer.clear()
        volume_finger_buffer.clear()
        music_close_buffer.clear()

    # ==========================
    # APP MODE
    # ==========================

    if mode == "APP":

        is_closed_fist = (
            hand_detected and finger_count == 0
        )

        closed_fist_buffer.append(is_closed_fist)

        stable_close = (
            len(closed_fist_buffer) == closed_fist_buffer.maxlen
            and all(closed_fist_buffer)
        )

        if stable_close and scroll_mode:

            print("CLOSE APP")

            close_app()

            scroll_mode = False

            selected_app = None
            selection_start_time = None

            closed_fist_buffer.clear()

        elif scroll_mode:

            two_hand_state = get_two_hand_state(
                hand_finger_counts
            )

            now = time.time()

            if (
                two_hand_state is not None
                and (now - last_scroll_time) >= SCROLL_COOLDOWN
            ):

                if two_hand_state == "BOTH_OPEN":

                    print("SCROLL UP (both hands open)")
                    scroll_up()

                elif two_hand_state == "ONE_OPEN_ONE_CLOSED":

                    print("SCROLL DOWN (one open, one fist)")
                    scroll_down()

                last_scroll_time = now

        else:

            (
                selected_app,
                selection_start_time,
                launched

            ) = handle_app_mode(

                finger_count,
                selected_app,
                selection_start_time
            )

            if launched:

                print(
                    f"Launched {selected_app}"
                )

                scroll_mode = True

                selected_app = None
                selection_start_time = None

    # ==========================
    # MUSIC MODE
    # ==========================

    elif mode == "MUSIC":

        now = time.time()

        # --------------------------
        # Two-hand: next / previous track
        # --------------------------

        two_hand_state = get_two_hand_state(
            hand_finger_counts
        )

        track_state_buffer.append(two_hand_state)

        stable_track_state = (
            len(track_state_buffer) == track_state_buffer.maxlen
            and all(
                s == track_state_buffer[0]
                for s in track_state_buffer
            )
            and track_state_buffer[0] in (
                "BOTH_OPEN",
                "BOTH_CLOSED"
            )
        )

        track_triggered = False

        if (
            stable_track_state
            and (now - last_track_time) >= TRACK_COOLDOWN
        ):

            if track_state_buffer[0] == "BOTH_OPEN":

                print("NEXT TRACK (both hands open)")

                next_track()

                track_triggered = True

            elif track_state_buffer[0] == "BOTH_CLOSED":

                print("PREVIOUS TRACK (both hands closed)")

                previous_track()

                track_triggered = True

            last_track_time = now

            selected_music_action = None
            music_action_start_time = None

            track_state_buffer.clear()

        # --------------------------
        # Single-hand: volume up / down / close window
        # --------------------------
        # Only runs when exactly one hand is visible, so none of
        # these can overlap with the two-hand track-switch gesture.

        if len(hand_finger_counts) == 1:

            single_fc = hand_finger_counts[0]

            # -- Volume (1 or 2 fingers) --

            volume_finger_buffer.append(single_fc)

            stable_volume_count = (
                len(volume_finger_buffer)
                == volume_finger_buffer.maxlen
                and all(
                    c == volume_finger_buffer[0]
                    for c in volume_finger_buffer
                )
            )

            if (
                stable_volume_count
                and volume_finger_buffer[0] in (1, 2)
                and (now - last_volume_time) >= VOLUME_COOLDOWN
            ):

                if volume_finger_buffer[0] == 1:

                    print("VOLUME UP (1 finger)")
                    volume_up()

                elif volume_finger_buffer[0] == 2:

                    print("VOLUME DOWN (2 fingers)")
                    volume_down()

                last_volume_time = now

            # -- Close window (3 fingers) --

            is_three_fingers = (single_fc == 3)

            music_close_buffer.append(is_three_fingers)

            stable_music_close = (
                len(music_close_buffer)
                == music_close_buffer.maxlen
                and all(music_close_buffer)
            )

            if (
                stable_music_close
                and (now - last_music_close_time)
                >= MUSIC_CLOSE_COOLDOWN
            ):

                print("CLOSE WINDOW (3 fingers, music mode)")

                close_app()

                last_music_close_time = now

                music_close_buffer.clear()

        else:

            volume_finger_buffer.clear()
            music_close_buffer.clear()

        # --------------------------
        # Fallback: play / pause (single-hand ML gesture)
        # --------------------------

        if not track_triggered:

            print("INSIDE MUSIC MODE")
            print("Current Gesture:", predicted_gesture)

            (
                selected_music_action,
                music_action_start_time,
                music_cooldown,
                music_cooldown_start,
                exit_mode

            ) = handle_music_mode(

                predicted_gesture,

                selected_music_action,
                music_action_start_time,

                music_cooldown,
                music_cooldown_start
            )

            # Mode-locking policy: gestures never exit a mode once
            # entered. exit_mode is intentionally ignored — only
            # quitting the program (Q) ends a session.

    # ==========================
    # Display
    # ==========================

    cv2.putText(
        frame,
        f"Gesture: {gesture}",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 0),
        2
    )

    cv2.putText(
        frame,
        f"Mode: {mode}",
        (20, 80),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 0, 0),
        2
    )

    cv2.putText(
        frame,
        f"Locked: {mode_locked}",
        (20, 120),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 0, 255),
        2
    )

    cv2.putText(
        frame,
        f"Fingers: {finger_count}",
        (20, 160),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 0),
        2
    )

    cv2.putText(
        frame,
        f"Selected App: {selected_app}",
        (20, 200),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 0, 255),
        2
    )

    cv2.putText(
        frame,
        f"Music Action: {selected_music_action}",
        (20, 240),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 255),
        2
    )

    cv2.putText(
        frame,
        f"Scroll Mode: {scroll_mode}",
        (20, 320),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2
    )

    cv2.putText(
        frame,
        f"Hands: {hand_finger_counts}",
        (20, 360),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 200, 255),
        2
    )

    cv2.putText(
        frame,
        "R = Reset | Q = Quit",
        (20, 280),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )

    cv2.imshow(
        "AI Gesture Controller",
        frame
    )

    key = cv2.waitKey(1) & 0xFF

    if key == ord('r'):

        mode = "NONE"
        mode_locked = False

        selected_app = None
        selection_start_time = None

        selected_music_action = None
        music_action_start_time = None

        scroll_mode = False

        gesture_buffer.clear()
        closed_fist_buffer.clear()
        track_state_buffer.clear()
        volume_finger_buffer.clear()
        music_close_buffer.clear()

    elif key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()