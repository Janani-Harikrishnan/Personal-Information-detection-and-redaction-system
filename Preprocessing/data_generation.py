import os
import numpy as np
from tensorflow.keras.preprocessing.image import ImageDataGenerator, load_img, img_to_array

# Paths
non_sensitive_dir = r"D:\5th sem\Deep Learning\Project\Data\Non_sensitive_Images"  # Original images
augmented_dir = r"D:\5th sem\Deep Learning\Project\Data\Non_sensitive_images"  # Output folder

os.makedirs(augmented_dir, exist_ok=True)

# Data augmentation configuration
datagen = ImageDataGenerator(
    rotation_range=30,
    width_shift_range=0.1,
    height_shift_range=0.1,
    zoom_range=0.1,
    horizontal_flip=True,
    fill_mode='nearest'
)

# Collect all images from folder and subfolders
images = []
for root, _, files in os.walk(non_sensitive_dir):
    for f in files:
        if f.lower().endswith(('.jpg', '.png')):
            images.append(os.path.join(root, f))

original_count = len(images)
print(f"Found {original_count} original non-sensitive images.")

# Number of images to generate
target_total = 7500
to_generate = target_total - original_count
if to_generate <= 0:
    print("No augmentation needed, you already have enough images.")
    exit()

# Calculate how many augmented images per original image
aug_per_image = int(np.ceil(to_generate / original_count))

print(f"Generating {to_generate} augmented images (~{aug_per_image} per original)...")

count = 0
for img_path in images:
    img = load_img(img_path)
    x = img_to_array(img)
    x = np.expand_dims(x, axis=0)

    i = 0
    for batch in datagen.flow(x, batch_size=1, save_to_dir=augmented_dir,
                              save_prefix='aug', save_format='jpg'):
        i += 1
        count += 1
        if i >= aug_per_image or count >= to_generate:
            break
    if count >= to_generate:
        break

print(f"✅ Augmentation complete. Total non-sensitive images: {original_count + count}")
