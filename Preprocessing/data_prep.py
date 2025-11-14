import os
from pdf2image import convert_from_path

# ---------------------- USER CONFIG ----------------------
# Root folder containing non-sensitive PDFs
non_sensitive_dir = r"D:\5th sem\Deep Learning\Project\Data\Non_sensitive"

# Root folder to save converted images
output_dir = r"D:\5th sem\Deep Learning\Project\Data\Non_sensitive_Images"

# Path to Poppler 'bin' folder
poppler_path = r"C:\Users\Ajai\Downloads\Release-25.07.0-0\poppler-25.07.0\Library\bin"  # <-- change this path if needed
# ---------------------------------------------------------

# Walk through all subfolders
for root, dirs, files in os.walk(non_sensitive_dir):
    # Compute relative path to maintain folder structure
    rel_path = os.path.relpath(root, non_sensitive_dir)
    save_path = os.path.join(output_dir, rel_path)
    os.makedirs(save_path, exist_ok=True)

    # Process all PDFs in this folder
    for f in files:
        if f.lower().endswith('.pdf'):
            pdf_path = os.path.join(root, f)
            try:
                pages = convert_from_path(pdf_path, poppler_path=poppler_path)
                for i, page in enumerate(pages):
                    img_name = f"{os.path.splitext(f)[0]}_page{i+1}.jpg"
                    page.save(os.path.join(save_path, img_name), 'JPEG')
                print(f"Converted {pdf_path} -> {len(pages)} images")
            except Exception as e:
                print(f"Error converting {pdf_path}: {e}")

print("All PDFs converted to images successfully!")
