import cv2
import mediapipe as mp
import joblib

# ==========================
# Load Trained Model
# ==========================

model = joblib.load("gesture_model.pkl")

# ==========================
# MediaPipe Setup
# ==========================

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# ==========================
# Webcam Setup
# ==========================

cap = cv2.VideoCapture(0)

if not cap.isOpened():

    print("Failed to open webcam")
    exit()

print("Gesture prediction started")

# ==========================
# Prediction Loop
# ==========================

while True:

    success, frame = cap.read()

    if not success:

        print("Failed to read frame")
        break

    # Mirror webcam frame

    frame = cv2.flip(frame, 1)

    rgb_frame = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )

    results = hands.process(rgb_frame)

    prediction = "NONE"

    # ==========================
    # Hand Detection
    # ==========================

    if results.multi_hand_landmarks:

        for hand_landmarks in results.multi_hand_landmarks:

            mp_draw.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS
            )

            # ==========================
            # Extract Landmark Features
            # ==========================

            features = []

            for landmark in hand_landmarks.landmark:

                features.extend([
                    landmark.x,
                    landmark.y,
                    landmark.z
                ])

            # ==========================
            # Gesture Prediction
            # ==========================

            prediction = model.predict(
                [features]
            )[0]

            print(
                "Predicted Gesture:",
                prediction
            )

    # ==========================
    # Display Prediction
    # ==========================

    cv2.putText(
        frame,
        f"Gesture: {prediction}",
        (20, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        2
    )

    cv2.putText(
        frame,
        "Q = Quit",
        (20, 90),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )

    cv2.imshow(
        "Gesture Prediction",
        frame
    )

    key = cv2.waitKey(1) & 0xFF

    if key == ord('q'):
        break

# ==========================
# Cleanup
# ==========================

cap.release()
hands.close()
cv2.destroyAllWindows()