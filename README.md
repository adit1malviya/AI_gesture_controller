# AI Gesture Controller

A real-time hand gesture control system that combines computer vision,
machine learning, and desktop automation to control applications and
media using hand gestures.

The project uses MediaPipe to extract hand landmarks, a custom-trained
Random Forest classifier for gesture recognition, and finger-count and
multi-hand logic for contextual desktop and media actions.

## Features

-   Real-time webcam-based hand tracking
-   Custom gesture dataset collection
-   Machine learning-based gesture recognition
-   Custom-trained Random Forest classifier
-   App Mode and Music Mode
-   Single-hand and two-hand gesture controls
-   Gesture smoothing and hold-time validation
-   Cooldown mechanisms to reduce repeated triggers
-   Desktop application launching and scrolling
-   Media playback and volume control
-   Context-aware YouTube seek controls
-   Live OpenCV status overlay
-   Standalone real-time gesture prediction script

## How It Works

``` text
Webcam Input
     |
     v
MediaPipe Hand Detection
     |
     v
21 Hand Landmarks
     |
     v
63 Coordinate Features (x, y, z)
     |
     v
Random Forest Classifier
     |
     v
Gesture Prediction
     |
     v
App Mode / Music Mode
     |
     v
Desktop and Media Actions
```

MediaPipe detects 21 hand landmarks. The `x`, `y`, and `z` coordinates
of every landmark are extracted to create 63 numerical features.

The trained machine learning model is used for gesture prediction and
mode selection. Finger-count and two-hand state logic are used for
contextual actions such as application selection, scrolling, volume
control, and track navigation.

## Custom Gesture Dataset

`main.py` is used to collect labeled gesture samples.

For every detected hand:

``` text
21 landmarks x 3 coordinates = 63 features
```

The 63 landmark coordinates are followed by the gesture label and
appended to:

``` text
dataset/gesture_data.csv
```

The current dataset contains approximately 1,466 gesture samples.

The dataset stores numerical hand-landmark coordinates rather than raw
hand images.

## Model Training

`train_model.py` loads the custom dataset using pandas and separates the
landmark coordinates from the gesture labels.

The training pipeline:

-   Uses 63 landmark coordinates as input features
-   Uses the final CSV column as the gesture label
-   Splits the dataset into 80% training data and 20% testing data
-   Uses `random_state=42`
-   Trains a `RandomForestClassifier`
-   Uses 100 estimators
-   Calculates test accuracy
-   Saves the trained classifier as `gesture_model.pkl` using Joblib

## Control Modes

The system provides two control modes.

  Gesture       Mode
  ------------- ------------
  Thumbs Down   App Mode
  Thumbs Up     Music Mode

Mode-selection predictions are stabilized across 5 consecutive frames
before a mode is activated.

Once selected, the mode remains locked for the current program session.

Press `Q` to quit the controller.

## App Mode

App Mode allows gesture-based application launching and scrolling.

Application selection must remain stable for 1 second before the
selected application is launched.

  Gesture                           Action
  --------------------------------- ------------------------------
  1 Finger                          Open Google Chrome
  2 Fingers                         Open Microsoft PowerPoint
  3 Fingers                         Open Microsoft Word
  4 Fingers                         Open Visual Studio Code
  Both Hands Open                   Scroll Up
  One Hand Open + One Hand Closed   Scroll Down
  Closed Fist held steadily         Close the active application

After an application is launched, App Mode enters scroll control.

A held closed fist closes the active application using `Alt + F4` and
returns App Mode to application selection.

## Music Mode

Music Mode provides playback, volume, track, and focused-window
controls.

  Gesture                       Action
  ----------------------------- -------------------------------------------
  Open Palm held for 1 second   Play / Pause
  1 Finger                      Volume Up
  2 Fingers                     Volume Down
  3 Fingers held steadily       Close the focused media window
  Both Hands Open               Next Track / Seek Forward on YouTube
  Both Hands Closed             Previous Track / Seek Backward on YouTube

### Context-Aware Media Control

The controller reads the title of the active Windows foreground window
using `win32gui`.

When YouTube is detected:

-   Both hands open sends the Right Arrow key and seeks forward by 5
    seconds.
-   Both hands closed sends the Left Arrow key and seeks backward by 5
    seconds.

For other media applications:

-   Both hands open sends the system Next Track command.
-   Both hands closed sends the system Previous Track command.

Play/Pause and volume controls use system media keys through PyAutoGUI.

## Gesture Stability and False-Trigger Prevention

The controller uses multiple validation mechanisms:

-   **Mode smoothing:** 5 consecutive matching predictions
-   **App selection hold:** 1 second
-   **Play/Pause hold:** 1 second
-   **Play/Pause cooldown:** 2 seconds
-   **Track gesture validation:** 6 consecutive frames
-   **Track cooldown:** 1.2 seconds
-   **Volume validation:** 4 consecutive stable finger-count frames
-   **Volume cooldown:** 0.4 seconds
-   **App close validation:** closed fist held for 8 frames
-   **Music window close validation:** 3 fingers held for 8 frames
-   **Music close cooldown:** 1.5 seconds

## Real-Time Gesture Prediction

`predict.py` provides a standalone real-time gesture prediction
interface.

It:

-   Opens the webcam
-   Mirrors the webcam frame
-   Detects one hand using MediaPipe
-   Extracts 63 landmark features
-   Loads `gesture_model.pkl`
-   Predicts the current gesture
-   Displays the predicted gesture in the OpenCV window

Press `Q` to close the prediction window.

## Project Structure

``` text
AI_Gesture_Controller/
|
|-- actions/
|   |-- app_controller.py
|   `-- music_controller.py
|
|-- controllers/
|   |-- app_mode.py
|   `-- music_mode.py
|
|-- dataset/
|   `-- gesture_data.csv
|
|-- .gitignore
|-- gesture_controller.py
|-- gesture_model.pkl
|-- main.py
|-- predict.py
|-- requirements.txt
`-- train_model.py
```

## File Overview

-   `gesture_controller.py` - Main real-time gesture controller and mode
    orchestration
-   `main.py` - Custom gesture dataset collection
-   `predict.py` - Standalone real-time gesture prediction and model
    testing
-   `train_model.py` - Random Forest model training and evaluation
-   `gesture_model.pkl` - Saved trained gesture classifier
-   `actions/app_controller.py` - Application launching, scrolling, and
    active-window closing
-   `actions/music_controller.py` - Media, volume, and context-aware
    YouTube controls
-   `controllers/app_mode.py` - App selection and hold-time logic
-   `controllers/music_mode.py` - Play/Pause hold-time and cooldown
    logic
-   `dataset/gesture_data.csv` - Custom hand-landmark gesture dataset
-   `requirements.txt` - Python project dependencies

## Tech Stack

-   Python
-   OpenCV
-   MediaPipe
-   Scikit-learn
-   pandas
-   Joblib
-   PyAutoGUI
-   pywin32

## Requirements

-   Windows
-   Python
-   Webcam
-   Google Chrome for the Chrome launch action
-   Microsoft PowerPoint for the PowerPoint launch action
-   Microsoft Word for the Word launch action
-   Visual Studio Code for the VS Code launch action

> The current application launcher uses Windows-specific executable
> paths, and active-window detection uses `pywin32`. The current version
> is designed for Windows.

## Installation

Clone the repository:

``` bash
git clone https://github.com/adit1malviya/AI_gesture_controller.git
```

Move into the project directory:

``` bash
cd AI_gesture_controller
```

Create a virtual environment:

``` bash
python -m venv venv
```

Activate the virtual environment in Windows PowerShell:

``` powershell
.\venv\Scripts\Activate.ps1
```

Install the dependencies:

``` bash
pip install -r requirements.txt
```

## Run the Gesture Controller

``` bash
python gesture_controller.py
```

Allow webcam access if prompted.

Show Thumbs Down to activate App Mode or Thumbs Up to activate Music
Mode.

Once a mode is selected, it remains locked for the current session.

Press `Q` in the OpenCV window to quit.

## Collect Gesture Data

Run:

``` bash
python main.py
```

Enter the gesture name when prompted:

``` text
Enter Gesture Name:
```

The script detects one hand, extracts its 63 landmark features, and
continuously appends labeled samples to `dataset/gesture_data.csv`.

Press `Q` to stop collecting data.

## Train the Model

Run:

``` bash
python train_model.py
```

The script prints the test accuracy and saves the trained classifier as:

``` text
gesture_model.pkl
```

## Test Gesture Prediction

Run:

``` bash
python predict.py
```

The live prediction window displays the gesture predicted by the trained
model.

Press `Q` to quit.

## Platform Support

The current version is Windows-focused because it uses:

-   Windows application executable paths
-   `pywin32` foreground-window detection
-   Windows media keys
-   `Alt + F4` window closing

## Author

**Aditi Malviya**

B.Tech Computer Science Engineering\
Graphic Era Deemed University

GitHub: `adit1malviya`
