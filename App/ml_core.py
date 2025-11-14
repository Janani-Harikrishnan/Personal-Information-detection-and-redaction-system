import torch
from torchvision import transforms, models
import torch.nn as nn
from PIL import Image
import cv2
import re
import os
import logging
from paddleocr import PaddleOCR
import numpy as np

# --- Configuration & Initialization ---

# Suppress PaddleOCR logging
logging.getLogger("ppocr").setLevel(logging.WARNING)

# Device setup
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Model path and image size
DL_MODEL_PATH = "efficientnetb3_best.pth"
IMAGE_SIZE = 300

model = None
ocr = None

# --- 1. Model Loading (PyTorch/EfficientNetB3) ---
try:
    # Recreate EfficientNetB3 architecture
    model = models.efficientnet_b3(weights=None)
    model.classifier = nn.Sequential(
        nn.Dropout(0.4),
        nn.Linear(model.classifier[1].in_features, 1),
        nn.Sigmoid()
    )
    model = model.to(device)
    
    # Locate weights (assuming the .pth file is in the same directory)
    # --- CORRECTED PATH LOGIC START (Option 2) ---
    # Assuming file structure: Project/Scripts/efficientnetb3_best.pth
    # and ml_core.py is in: Project/FlaskApp/
    
    # 1. Get the directory of the currently executing script (e.g., Project/FlaskApp)
    core_dir = os.path.dirname(os.path.abspath(__file__))
    # 2. Go up one directory to reach the project root (Project/)
    project_root_dir = os.path.dirname(core_dir)
    # 3. Construct the path to the Scripts folder
    scripts_dir = os.path.join(project_root_dir, "Scripts")
    # 4. Final path to the model weights
    weights_path = os.path.join(scripts_dir, DL_MODEL_PATH)
    # --- CORRECTED PATH LOGIC END ---

    
    # Load weights
    model.load_state_dict(torch.load(weights_path, map_location=device))
    model.eval()
    print("✅ PyTorch model loaded successfully in ml_core.")
    
except Exception as e:
    # Use the DL_MODEL_PATH variable here for clearer error logging
    print(f"❌ ERROR in ml_core: Failed to load PyTorch model weights from {DL_MODEL_PATH} (Looking in: {weights_path}). Reason: {e}")
    model = None

# --- 2. Preprocessing (Torchvision) ---
transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.ToTensor(),
])

# --- 3. OCR Initialization (PaddleOCR) ---
try:
    # Initialize PaddleOCR (This might download models if run for the first time)
    ocr = PaddleOCR(use_angle_cls=True, lang='en')
    print("✅ PaddleOCR initialized successfully in ml_core.")
except Exception as e:
    print(f"❌ ERROR in ml_core: Failed to initialize PaddleOCR. Reason: {e}")
    ocr = None

# Regex patterns
aadhaar_pattern = r"\d{4}\s?\d{4}\s?\d{4}"
pan_pattern = r"[A-Z]{5}[0-9]{4}[A-Z]"


# --- 4. Prediction Logic ---

def predict_image(image_path: str) -> tuple[str, float]:
    """Classifies the image as Sensitive or Non-sensitive."""
    if model is None:
        raise RuntimeError("Classification model is not loaded in ml_core.")
    
    image = Image.open(image_path).convert("RGB")
    image = transform(image).unsqueeze(0).to(device)

    with torch.no_grad():
        prob = model(image).item()
        pred = 1 if prob > 0.5 else 0

    label = "Sensitive" if pred == 1 else "Non-Sensitive"
    return label, prob


def redact_sensitive_info(image_path: str, output_path: str) -> None:
    """Detects and redacts sensitive info using PaddleOCR, saving output to output_path."""
    if ocr is None:
        raise RuntimeError("PaddleOCR is not initialized in ml_core.")

    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"OpenCV failed to read image at: {image_path}")

    results = ocr.ocr(image_path, cls=True)
    
    # Check if results is not empty and has the expected structure
    if not results or not results[0]:
        cv2.imwrite(output_path, img) # Save original if OCR fails
        return

    # Loop through detected text
    for line in results[0]:
        if line is None or len(line) < 2:
            continue

        bbox = line[0]  # Bounding box points
        text = line[1][0]
        conf = line[1][1]

        if conf < 0.4:
            continue

        clean_text = text.replace(" ", "").upper()
        is_sensitive = False

        # Check for PAN
        if re.fullmatch(pan_pattern, clean_text):
            is_sensitive = True
        
        # Check for Aadhaar
        aadhaar_clean = text.replace(" ", "")
        if re.fullmatch(aadhaar_pattern, aadhaar_clean):
            is_sensitive = True

        if is_sensitive:
            # Redaction logic
            pts = [(int(x), int(y)) for x, y in bbox]
            x_min, y_min = int(min([p[0] for p in pts])), int(min([p[1] for p in pts]))
            x_max, y_max = int(max([p[0] for p in pts])), int(max([p[1] for p in pts]))
            
            # Ensure boundaries are valid
            x_min, y_min = max(0, x_min), max(0, y_min)
            x_max, y_max = min(img.shape[1], x_max), min(img.shape[0], y_max)

            roi = img[y_min:y_max, x_min:x_max]
            
            if roi.size > 0:
                k = max(23, (x_max - x_min) // 2 | 1, (y_max - y_min) // 2 | 1)
                img[y_min:y_max, x_min:x_max] = cv2.GaussianBlur(roi, (k, k), 30)

    # Save redacted image to the specified output path
    cv2.imwrite(output_path, img)
