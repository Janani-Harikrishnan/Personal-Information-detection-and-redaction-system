import os
import shutil
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight
from PIL import Image
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms, models
from tqdm import tqdm

# -------------------------------
# 1. Paths Setup
# -------------------------------
BASE_DIR = r"D:\5th sem\Deep Learning\Project\Data"
NON_SENSITIVE_DIR = os.path.join(BASE_DIR, "Non_sensitive_Images")
SENSITIVE_DIR = os.path.join(BASE_DIR, "Sensitive", "acw-90")

DATASET_DIR = os.path.join(BASE_DIR, "Final_Data")
TRAIN_DIR = os.path.join(DATASET_DIR, "train")
VAL_DIR = os.path.join(DATASET_DIR, "val")
TEST_DIR = os.path.join(DATASET_DIR, "test")

# -------------------------------
# 2. Create Final Dataset Structure
# -------------------------------
if not os.path.exists(DATASET_DIR):
    os.makedirs(TRAIN_DIR), os.makedirs(VAL_DIR), os.makedirs(TEST_DIR)

    # Get image paths
    non_sensitive_imgs = [os.path.join(NON_SENSITIVE_DIR, img) for img in os.listdir(NON_SENSITIVE_DIR)]
    sensitive_imgs = [os.path.join(SENSITIVE_DIR, img) for img in os.listdir(SENSITIVE_DIR)]

    # Labels
    non_sensitive_labels = ["non_sensitive"] * len(non_sensitive_imgs)
    sensitive_labels = ["sensitive"] * len(sensitive_imgs)

    X = np.array(non_sensitive_imgs + sensitive_imgs)
    y = np.array(non_sensitive_labels + sensitive_labels)

    # Split train, val, test
    X_train, X_tmp, y_train, y_tmp = train_test_split(X, y, test_size=0.3, stratify=y, random_state=42)
    X_val, X_test, y_val, y_test = train_test_split(X_tmp, y_tmp, test_size=0.5, stratify=y_tmp, random_state=42)

    def copy_files(X, y, dest_dir):
        for img_path, label in zip(X, y):
            label_dir = os.path.join(dest_dir, label)
            os.makedirs(label_dir, exist_ok=True)
            shutil.copy(img_path, label_dir)

    copy_files(X_train, y_train, TRAIN_DIR)
    copy_files(X_val, y_val, VAL_DIR)
    copy_files(X_test, y_test, TEST_DIR)

    print("✅ Dataset successfully organized!")

# -------------------------------
# 3. PyTorch Dataset & DataLoader
# -------------------------------
IMAGE_SIZE = 300
BATCH_SIZE = 32

class ImageFolderDataset(Dataset):
    def __init__(self, root_dir, transform=None):
        self.samples = []
        self.labels_map = {"non_sensitive": 0, "sensitive": 1}
        for label in ["non_sensitive", "sensitive"]:
            folder = os.path.join(root_dir, label)
            for img_name in os.listdir(folder):
                self.samples.append((os.path.join(folder, img_name), self.labels_map[label]))
        self.transform = transform

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        img_path, label = self.samples[idx]
        image = Image.open(img_path).convert("RGB")
        if self.transform:
            image = self.transform(image)
        return image, label

# Transforms
train_transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(20),
    transforms.ToTensor(),
])

val_test_transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.ToTensor(),
])

# Datasets
train_dataset = ImageFolderDataset(TRAIN_DIR, transform=train_transform)
val_dataset = ImageFolderDataset(VAL_DIR, transform=val_test_transform)
test_dataset = ImageFolderDataset(TEST_DIR, transform=val_test_transform)

# Compute class weights
labels = [label for _, label in train_dataset.samples]
class_weights = compute_class_weight(class_weight="balanced", classes=np.unique(labels), y=labels)
class_weights = torch.tensor(class_weights, dtype=torch.float32)
print("⚖ Class Weights:", class_weights.numpy())

# DataLoaders
train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE)
test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE)

# -------------------------------
# 4. Model Setup (EfficientNetB3)
# -------------------------------
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = models.efficientnet_b3(pretrained=True)
for param in model.features.parameters():
    param.requires_grad = False  # Freeze base layers

# Replace classifier
model.classifier = nn.Sequential(
    nn.Dropout(0.4),
    nn.Linear(model.classifier[1].in_features, 1),
    nn.Sigmoid()
)
model = model.to(device)

# Loss and optimizer
criterion = nn.BCELoss()
optimizer = optim.Adam(model.classifier.parameters(), lr=1e-4)

# -------------------------------
# 5. Training Loop with Progress Bar
# -------------------------------
EPOCHS = 25
best_val_loss = float("inf")

for epoch in range(EPOCHS):
    # Training
    model.train()
    train_loss = 0
    correct = 0
    total = 0
    train_bar = tqdm(train_loader, desc=f"Epoch {epoch+1}/{EPOCHS} [Train]", leave=False)
    
    for images, labels in train_bar:
        images, labels = images.to(device), labels.float().to(device).unsqueeze(1)
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        train_loss += loss.item() * images.size(0)
        preds = (outputs > 0.5).float()
        correct += (preds == labels).sum().item()
        total += labels.size(0)

        train_bar.set_postfix(loss=train_loss/total, acc=correct/total)

    train_acc = correct / total
    train_loss /= total

    # Validation
    model.eval()
    val_loss = 0
    correct = 0
    total = 0
    val_bar = tqdm(val_loader, desc=f"Epoch {epoch+1}/{EPOCHS} [Val]  ", leave=False)
    with torch.no_grad():
        for images, labels in val_bar:
            images, labels = images.to(device), labels.float().to(device).unsqueeze(1)
            outputs = model(images)
            loss = criterion(outputs, labels)

            val_loss += loss.item() * images.size(0)
            preds = (outputs > 0.5).float()
            correct += (preds == labels).sum().item()
            total += labels.size(0)

            val_bar.set_postfix(loss=val_loss/total, acc=correct/total)

    val_acc = correct / total
    val_loss /= total

    print(f"Epoch {epoch+1}/{EPOCHS}: Train Loss {train_loss:.4f}, Train Acc {train_acc:.4f}, Val Loss {val_loss:.4f}, Val Acc {val_acc:.4f}")

    # Save best model
    if val_loss < best_val_loss:
        torch.save(model.state_dict(), "efficientnetb3_best.pth")
        best_val_loss = val_loss

# -------------------------------
# 6. Test Evaluation
# -------------------------------
model.load_state_dict(torch.load("efficientnetb3_best.pth"))
model.eval()
correct = 0
total = 0
with torch.no_grad():
    for images, labels in test_loader:
        images, labels = images.to(device), labels.float().to(device).unsqueeze(1)
        outputs = model(images)
        preds = (outputs > 0.5).float()
        correct += (preds == labels).sum().item()
        total += labels.size(0)
test_acc = correct / total
print(f"✅ Test Accuracy: {test_acc:.4f}")

