import torch
from torchvision import transforms, models
from PIL import Image
import torch.nn as nn
import cv2
import re
import os
from paddleocr import PaddleOCR
import logging

logging.getLogger("ppocr").setLevel(logging.WARNING)

# -------------------------------
# 1. Load trained classification model
# -------------------------------
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Recreate EfficientNetB3 architecture
model = models.efficientnet_b3(weights=None)
model.classifier = nn.Sequential(
    nn.Dropout(0.4),
    nn.Linear(model.classifier[1].in_features, 1),
    nn.Sigmoid()
)
model = model.to(device)

# Load saved weights
script_dir = os.path.dirname(os.path.abspath(__file__))
weights_path = os.path.join(script_dir, "efficientnetb3_best.pth")
model.load_state_dict(torch.load(weights_path, map_location=device))
model.eval()

# -------------------------------
# 2. Define preprocessing
# -------------------------------
IMAGE_SIZE = 300
transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.ToTensor(),
])

# -------------------------------
# 3. Initialize PaddleOCR
# -------------------------------
ocr = PaddleOCR(use_angle_cls=True, lang='en')  # English OCR

# Regex patterns
aadhaar_pattern = r"\d{4}\s?\d{4}\s?\d{4}"
pan_pattern = r"[A-Z]{5}[0-9]{4}[A-Z]"

# -------------------------------
# 4. Redaction function using PaddleOCR
# -------------------------------
def redact_sensitive_info(image_path):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    img = cv2.imread(image_path)

    # Run OCR
    results = ocr.ocr(image_path, cls=True)
    sensitive_found = False

    # Loop through detected text
    for line in results[0]:
        bbox = line[0]  # Bounding box points
        text = line[1][0]
        conf = line[1][1]

        if conf < 0.4:  # Ignore low-confidence results
            continue

        clean_text = text.replace(" ", "").upper()

        # ----- Check for PAN -----
        if re.fullmatch(pan_pattern, clean_text):
            sensitive_found = True
            print(f"--> Blurring PAN: {text}")
            pts = [(int(x), int(y)) for x, y in bbox]
            x_min, y_min = int(min([p[0] for p in pts])), int(min([p[1] for p in pts]))
            x_max, y_max = int(max([p[0] for p in pts])), int(max([p[1] for p in pts]))
            roi = img[y_min:y_max, x_min:x_max]
            if roi.size > 0:
                k = max(23, (x_max - x_min) // 2 | 1, (y_max - y_min) // 2 | 1)
                img[y_min:y_max, x_min:x_max] = cv2.GaussianBlur(roi, (k, k), 30)

        # ----- Check for Aadhaar -----
        aadhaar_clean = text.replace(" ", "")
        if re.fullmatch(aadhaar_pattern, aadhaar_clean):
            sensitive_found = True
            print(f"--> Blurring Aadhaar: {text}")
            pts = [(int(x), int(y)) for x, y in bbox]
            x_min, y_min = int(min([p[0] for p in pts])), int(min([p[1] for p in pts]))
            x_max, y_max = int(max([p[0] for p in pts])), int(max([p[1] for p in pts]))
            roi = img[y_min:y_max, x_min:x_max]
            if roi.size > 0:
                k = max(23, (x_max - x_min) // 2 | 1, (y_max - y_min) // 2 | 1)
                img[y_min:y_max, x_min:x_max] = cv2.GaussianBlur(roi, (k, k), 30)

    # Save redacted image
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    output_path = os.path.join(script_dir, f"{base_name}_redacted.png")
    cv2.imwrite(output_path, img)
    print(f"✅ Redacted image saved at: {output_path}")

    # Save debug OCR image
    debug_img = img.copy()
    for line in results[0]:
        bbox = line[0]
        text = line[1][0]
        conf = line[1][1]
        if conf > 0.4:
            pts = [(int(x), int(y)) for x, y in bbox]
            for i in range(4):
                cv2.line(debug_img, pts[i], pts[(i + 1) % 4], (0, 255, 0), 2)
            cv2.putText(
                debug_img,
                text,
                (pts[0][0], pts[0][1] - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 0, 255),
                1
            )

    debug_path = os.path.join(script_dir, "ocr_debug.png")
    cv2.imwrite(debug_path, debug_img)
    print(f"🔍 Debug OCR image saved at: {debug_path}")


# -------------------------------
# 5. Prediction function
# -------------------------------
def predict_image(image_path):
    image = Image.open(image_path).convert("RGB")
    image = transform(image).unsqueeze(0).to(device)

    with torch.no_grad():
        prob = model(image).item()
        pred = 1 if prob > 0.5 else 0

    label = "Sensitive" if pred == 1 else "Non-sensitive"
    return label, prob


# -------------------------------
# 6. Run workflow on a test image
# -------------------------------
if __name__ == "__main__":
    img_path = r"D:\5th sem\Deep Learning\Project\Data\Sensitive\cw-180\0_1f398.jpg"

    label, prob = predict_image(img_path)
    print(f"Prediction: {label} (Probability: {prob:.4f})")

    if label == "Sensitive":
        redact_sensitive_info(img_path)
    else:
        print("Image is non-sensitive, no redaction needed ✅")
