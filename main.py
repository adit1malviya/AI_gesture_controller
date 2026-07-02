import cv2
import mediapipe as mp
import csv

print("Program started")

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands()

print("MediaPipe initialized")

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Failed to open webcam")
    exit()

print("Webcam opened successfully")

gesture_label = input("Enter Gesture Name: ")
print(f"Gesture entered: {gesture_label}")

with open("dataset/gesture_data.csv", "a", newline="") as f:

    writer = csv.writer(f)

    print("CSV file opened")

    while True:

        success, frame = cap.read()

        if not success:
            print("Failed to read frame")
            break

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        results = hands.process(rgb_frame)

        if results.multi_hand_landmarks:

            for hand_landmarks in results.multi_hand_landmarks:

                mp_draw.draw_landmarks(
                    frame,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS
                )

                row = []

                for landmark in hand_landmarks.landmark:

                    row.extend([
                        landmark.x,
                        landmark.y,
                        landmark.z
                    ])

                row.append(gesture_label)

                writer.writerow(row)

        cv2.imshow("Dataset Collection", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("Exiting...")
            break

cap.release()
cv2.destroyAllWindows()