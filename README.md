An AI-powered system that automatically detects and redacts Personally Identifiable Information (PII) from documents such as Aadhaar and PAN cards. The system combines deep learning, OCR, and rule-based methods to securely remove sensitive details and generate redacted outputs in real time.

 Features

- Detects PII (Aadhaar, PAN, names, dates, phone numbers, etc.)

- EfficientNet-B3 for document classification

- PaddleOCR for extracting text + coordinates

- Automated redaction using OpenCV

- Fast processing (< 2 seconds per document)

- Simple Flask web app for uploads and results

- Ensures privacy and prevents sensitive data exposure


How It Works

Upload document (Aadhaar/PAN).

Model identifies document type using EfficientNet-B3.

PaddleOCR extracts text and bounding boxes.

Regex + rules detect PII fields.

OpenCV redacts sensitive regions.

User downloads the clean redacted document.