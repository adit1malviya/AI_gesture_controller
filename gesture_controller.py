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
    scroll_down
)

from actions.music_controller import (
    next_track,
    previous_track
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
# Closed-Fist Smoothing (for APP mode exit)
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
# Requires the pose to be held for TRACK_HOLD_FRAMES consecutive
# frames before triggering, then a cooldown before it can fire again.
# This stops a brief hand-crossing motion from accidentally
# switching tracks.

TRACK_HOLD_FRAMES = 6
TRACK_COOLDOWN = 1.2

track_state_buffer = deque(maxlen=TRACK_HOLD_FRAMES)
last_track_time = 0

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

                if not mode_locked:

                    if stable_gesture == "THUMBS_DOWN":

                        mode = "APP"
                        mode_locked = True

                        print("APP MODE")

                    elif stable_gesture == "THUMBS_UP":

                        mode = "MUSIC"
                        mode_locked = True

                        print("MUSIC MODE")

                    elif stable_gesture == "OPEN_PALM":

                        mode = "EDIT"
                        mode_locked = True

                        print("EDIT MODE")

    else:

        gesture_buffer.clear()
        closed_fist_buffer.clear()
        track_state_buffer.clear()

    # ==========================
    # APP MODE
    # ==========================

    if mode == "APP":

        is_closed_fist = (
            hand_detected and finger_count == 0
        )

        closed_fist_buffer.append(is_closed_fist)

        stable_exit = (
            len(closed_fist_buffer) == closed_fist_buffer.maxlen
            and all(closed_fist_buffer)
        )

        if stable_exit:

            print("EXIT APP MODE")

            mode = "NONE"
            mode_locked = False

            scroll_mode = False

            selected_app = None
            selection_start_time = None

            closed_fist_buffer.clear()

        elif scroll_mode:

            # Two-hand scroll gesture

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

            # Still choosing which app to open

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

        two_hand_state = get_two_hand_state(
            hand_finger_counts
        )

        # Only BOTH_OPEN / BOTH_CLOSED matter here — a single hand
        # plus nothing (or a stray second hand) should fall through
        # to normal single-hand play/pause / exit handling below.

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

        now = time.time()

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

            # Reset single-hand play/pause timer so it doesn't
            # also fire from the same open-palm pose.
            selected_music_action = None
            music_action_start_time = None

            track_state_buffer.clear()

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

            if exit_mode:

                print(
                    "Exited Music Mode"
                )

                mode = "NONE"
                mode_locked = False

                selected_music_action = None
                music_action_start_time = None

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

    elif key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()