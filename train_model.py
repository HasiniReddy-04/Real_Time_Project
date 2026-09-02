from sklearn.tree import DecisionTreeClassifier
import joblib

# Sample training data
# [score, programming_interest, data_interest, design_interest]

X = [
    [90, 5, 4, 1],
    [80, 4, 5, 1],
    [70, 3, 4, 2],
    [60, 3, 2, 1],
    [50, 2, 2, 2],
    [40, 1, 1, 3],
    [30, 1, 0, 4],
    [20, 0, 0, 5]
]

y = [
    "Data Scientist",
    "Data Scientist",
    "Software Developer",
    "Software Developer",
    "Software Developer",
    "Designer",
    "Designer",
    "Designer"
]

# Train model
model = DecisionTreeClassifier()
model.fit(X, y)

# Save model
joblib.dump(model, "model.pkl")

print("Model trained and saved successfully ✅")