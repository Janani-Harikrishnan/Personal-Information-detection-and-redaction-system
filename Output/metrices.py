import torch
import torch.nn as nn
from torchvision import transforms, models
from PIL import Image
from sklearn.metrics import f1_score, accuracy_score, precision_score, recall_score, confusion_matrix
import numpy as np
import os
import sys

# --- Configuration (Must match ml_core.py setup) ---

# Device setup
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Model path and image size
DL_MODEL_PATH = "efficientnetb3_best.pth"
IMAGE_SIZE = 300
CLASSIFICATION_THRESHOLD = 0.5  # Threshold for converting probability to binary prediction (0 or 1)

# --- CORRECTED TEST DATA DIRECTORY CALCULATION ---
# This code block sets the absolute path for your test data.
# Note: PROJECT_ROOT and SCRIPT_DIR are retained for model path calculation.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR)) 
TEST_DATA_DIR = r"D:\5th sem\Deep Learning\Project\Data\Final_Data\test" 
# --- END CORRECTED PATH CALCULATION ---


# --- 1. Model Loading Function ---

def load_classification_model(weights_path: str):
    """Recreates the model architecture and loads saved weights."""
    try:
        # Recreate EfficientNetB3 architecture
        model = models.efficientnet_b3(weights=None)
        
        # Modify the classifier head (as done in your training/testing script)
        model.classifier = nn.Sequential(
            nn.Dropout(0.4),
            nn.Linear(model.classifier[1].in_features, 1),
            nn.Sigmoid()
        )
        model = model.to(device)

        # Locate weights: Assumes model is in 'Project/Scripts/'
        scripts_dir = r"D:\5th sem\Deep Learning\Project\Scripts"
        weights_full_path = os.path.join(scripts_dir, weights_path)

        model.load_state_dict(torch.load(weights_full_path, map_location=device))
        model.eval()
        print(f"✅ Model loaded successfully from: {weights_full_path}")
        return model
        
    except Exception as e:
        # Note: Using the dynamically calculated path in the error message
        print(f"❌ ERROR: Failed to load PyTorch model weights from {weights_full_path}. Reason: {e}")
        return None

# --- 2. Data Preparation ---

# Define the image preprocessing transform
transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.ToTensor(),
])

def load_test_data_from_folders(base_dir: str) -> list[tuple[str, int]]:
    """
    Scans 'sensitive' and 'non_sensitive' subfolders for test images.
    """
    test_data = []
    
    # Define mapping: Folder Name -> True Label
    label_map = {
        "non_sensitive": 0,  # Predicted 0 is Non-Sensitive
        "sensitive": 1       # Predicted 1 is Sensitive
    }
    
    if not os.path.isdir(base_dir):
        print(f"🛑 Error: Test data directory not found at: {base_dir}")
        return test_data

    print(f"Scanning test data in: {base_dir}")

    for folder_name, true_label in label_map.items():
        # Case-insensitive path join to match 'sensitive' or 'Sensitive'
        folder_path = os.path.join(base_dir, folder_name)
        if not os.path.isdir(folder_path):
            # Check for title-case version if lowercase failed
            folder_path = os.path.join(base_dir, folder_name.capitalize())

        if not os.path.isdir(folder_path):
            print(f"   Warning: Subfolder '{folder_name}' not found. Skipping label {true_label}.")
            continue

        for filename in os.listdir(folder_path):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                image_path = os.path.join(folder_path, filename)
                test_data.append((image_path, true_label))
    
    print(f"Found {len(test_data)} total images for evaluation.")
    return test_data


# --- 3. Prediction Function ---

def make_prediction(model, image_path: str) -> float:
    """Processes a single image and returns the probability score."""
    if model is None:
        # This RuntimeError should only occur if the initial load failed.
        raise RuntimeError("Model is not loaded. Cannot make prediction.")
    
    try:
        # Check if the image file actually exists
        if not os.path.exists(image_path):
             print(f"Warning: Image file not found: {image_path}. Skipping.")
             return 0.0

        image = Image.open(image_path).convert("RGB")
        image = transform(image).unsqueeze(0).to(device)

        with torch.no_grad():
            prob = model(image).item()
        return prob
        
    except Exception as e:
        print(f"Warning: Could not process image {os.path.basename(image_path)}. Error: {e}")
        return 0.0


# --- 4. Main Evaluation Block ---

if __name__ == "__main__":
    
    # Load the model once
    model = load_classification_model(DL_MODEL_PATH)
    
    if model is None:
        sys.exit("Evaluation stopped due to model loading error.")

    # Load data automatically from the specified directory structure
    TEST_DATA = load_test_data_from_folders(TEST_DATA_DIR)
    
    if not TEST_DATA:
        print("🛑 WARNING: No test data found. Please ensure the directory is correct and contains 'sensitive' and 'non_sensitive' subfolders.")
        sys.exit()

    true_labels = []
    predicted_probabilities = []

    print("\nStarting evaluation across test dataset...")
    
    for img_path, true_label in TEST_DATA:
        prob = make_prediction(model, img_path)
        predicted_probabilities.append(prob)
        true_labels.append(true_label)

    # Convert probabilities to binary predictions
    predicted_labels = (np.array(predicted_probabilities) > CLASSIFICATION_THRESHOLD).astype(int)

    # --- 5. Calculate Metrics ---
    
    print("\n" + "="*40)
    print(f"CLASSIFICATION PERFORMANCE METRICS (Threshold: {CLASSIFICATION_THRESHOLD})")
    print("="*40)
    
    # Accuracy
    accuracy = accuracy_score(true_labels, predicted_labels)
    print(f"Accuracy (Overall Correctness): {accuracy:.4f}")

    # Precision
    precision = precision_score(true_labels, predicted_labels, zero_division=0)
    print(f"Precision (Low False Positives): {precision:.4f}")
    
    # Recall
    recall = recall_score(true_labels, predicted_labels, zero_division=0)
    print(f"Recall (Low False Negatives): {recall:.4f}")

    # F1 Score (Harmonic mean of Precision and Recall)
    f1 = f1_score(true_labels, predicted_labels, zero_division=0)
    print(f"F1 Score (Balanced Metric): {f1:.4f}")
    
    print(f"\nEvaluation Complete.")
