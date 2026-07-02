import joblib
import pandas as pd

# Check what labels the trained model actually knows
model = joblib.load("gesture_model.pkl")
print("Model's known classes:")
for c in model.classes_:
    print(f"  '{c}'")

# Check what labels exist in your training CSV
df = pd.read_csv("dataset/gesture_data.csv", header=None)
label_col = df.iloc[:, -1]
print("\nUnique labels in gesture_data.csv:")
for label in label_col.unique():
    print(f"  '{label}'")