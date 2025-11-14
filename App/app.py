import os
import sys
import tempfile
import base64
from flask import Flask, request, jsonify, render_template_string

# Adjust this import based on where you save ml_core.py (or testing.py)
# If you rename 'ml_core.py' to 'testing.py' and place it in a subdirectory 
# like the user's original path, you would use: from testing import predict_image, redact_sensitive_info
# For simplicity, we assume ml_core.py is in the current directory.
try:
    from ml_core import predict_image, redact_sensitive_info
except ImportError:
    # Fallback/Error handling if ml_core.py is not found.
    print("ERROR: Could not import ml_core.py. Ensure it is in the same directory.")
    sys.exit(1)


app = Flask(__name__)

# --- HTML/CSS/JS FRONT-END (SINGLE-FILE STRATEGY) ---
# Your entire frontend code is stored here for serving.
HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Document Privacy Scanner - AI-Powered Sensitive Information Detection</title>
    <meta name="description" content="Automatically detect and protect sensitive information in documents using AI. Upload PAN cards, Aadhaar, tickets, bills and get privacy-protected versions instantly.">
    <meta name="author" content="Document Privacy Scanner">
    
    <!-- Open Graph Meta Tags -->
    <meta property="og:title" content="Document Privacy Scanner - AI-Powered Privacy Protection">
    <meta property="og:description" content="Automatically detect and protect sensitive information in documents using AI. Upload PAN cards, Aadhaar, tickets, bills and get privacy-protected versions instantly.">
    <meta property="og:type" content="website">
    
    <!-- Lucide Icons -->
    <script src="https://unpkg.com/lucide@latest/dist/umd/lucide.js"></script>

    <!-- CSS Inlined -->
    <style>
        /* CSS Variables - Design System */
        :root {
            /* Colors */
            --background: hsl(240, 10%, 98%);
            --foreground: hsl(240, 10%, 9%);
            --card: hsl(0, 0%, 100%);
            --card-foreground: hsl(240, 10%, 9%);
            --primary: hsl(217, 91%, 60%);
            --primary-foreground: hsl(0, 0%, 100%);
            --primary-glow: hsl(217, 91%, 70%);
            --secondary: hsl(240, 5%, 96%);
            --secondary-foreground: hsl(240, 6%, 10%);
            --muted: hsl(240, 5%, 96%);
            --muted-foreground: hsl(240, 4%, 46%);
            --accent: hsl(217, 91%, 95%);
            --accent-foreground: hsl(217, 91%, 60%);
            --destructive: hsl(0, 84%, 60%);
            --destructive-foreground: hsl(0, 0%, 100%);
            --success: hsl(142, 76%, 36%);
            --success-foreground: hsl(0, 0%, 100%);
            --warning: hsl(38, 92%, 50%);
            --warning-foreground: hsl(0, 0%, 100%);
            --border: hsl(240, 6%, 90%);
            --input: hsl(240, 6%, 90%);
            --ring: hsl(217, 91%, 60%);

            /* Gradients */
            --gradient-primary: linear-gradient(135deg, hsl(217, 91%, 60%) 0%, hsl(217, 91%, 70%) 100%);
            --gradient-secondary: linear-gradient(135deg, hsl(240, 5%, 96%) 0%, hsl(240, 6%, 90%) 100%);
            --gradient-hero: linear-gradient(135deg, hsl(217, 91%, 60%) 0%, hsl(234, 89%, 74%) 50%, hsl(217, 91%, 70%) 100%);

            /* Shadows */
            --shadow-soft: 0 2px 8px -2px hsl(240, 10%, 9%, 0.04);
            --shadow-medium: 0 4px 16px -4px hsl(240, 10%, 9%, 0.08);
            --shadow-large: 0 8px 32px -8px hsl(240, 10%, 9%, 0.12);
            --shadow-glow: 0 0 24px hsl(217, 91%, 60%, 0.3);

            /* Animations */
            --transition-smooth: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            --transition-spring: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);

            /* Spacing */
            --radius: 0.5rem;
        }

        /* Base Styles */
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background-color: var(--background);
            color: var(--foreground);
            line-height: 1.6;
            min-height: 100vh;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 1rem;
        }

        /* Header */
        .header {
            background: hsl(var(--card) / 0.5);
            backdrop-filter: blur(8px);
            border-bottom: 1px solid var(--border);
            position: sticky;
            top: 0;
            z-index: 10;
        }

        .header-content {
            padding: 1.5rem 0;
        }

        .logo {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .logo-icon {
            background: var(--gradient-primary);
            padding: 0.5rem;
            border-radius: var(--radius);
            color: var(--primary-foreground);
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .logo-icon i {
            width: 24px;
            height: 24px;
        }

        .logo-text h1 {
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 0.25rem;
        }

        .logo-text p {
            color: var(--muted-foreground);
            font-size: 0.875rem;
        }

        /* Main Container */
        .main-container {
            max-width: 1000px;
            margin: 0 auto;
            padding: 2rem 1rem;
        }

        /* Features Grid */
        .features-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }

        .feature-card {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 1.5rem;
            text-align: center;
            box-shadow: var(--shadow-soft);
            transition: var(--transition-smooth);
        }

        .feature-card:hover {
            box-shadow: var(--shadow-medium);
            transform: translateY(-2px);
        }

        .feature-icon {
            background: hsl(var(--primary) / 0.1);
            color: var(--primary);
            width: 48px;
            height: 48px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 1rem;
        }

        .feature-card h3 {
            font-size: 1.125rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }

        .feature-card p {
            color: var(--muted-foreground);
            font-size: 0.875rem;
        }

        /* Separator */
        .separator {
            height: 1px;
            background: var(--border);
            margin: 2rem 0;
        }

        /* Upload Section */
        .upload-content {
            max-width: 600px;
            margin: 0 auto;
        }

        .upload-header {
            text-align: center;
            margin-bottom: 2rem;
        }

        .upload-header h2 {
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }

        .upload-header p {
            color: var(--muted-foreground);
            font-size: 1rem;
        }

        /* Upload Zone */
        .upload-zone {
            background: var(--card);
            border: 2px dashed var(--border);
            border-radius: var(--radius);
            padding: 2rem;
            text-align: center;
            cursor: pointer;
            transition: var(--transition-smooth);
            margin-bottom: 1.5rem;
        }

        .upload-zone:hover {
            border-color: hsl(var(--primary) / 0.5);
            box-shadow: var(--shadow-medium);
        }

        .upload-zone.drag-over {
            border-color: var(--primary);
            background: var(--accent);
            box-shadow: var(--shadow-glow);
        }

        .upload-zone-content {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 1rem;
        }

        .upload-icon {
            background: var(--muted);
            color: var(--muted-foreground);
            width: 64px;
            height: 64px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: var(--transition-smooth);
        }

        .upload-zone.drag-over .upload-icon {
            background: var(--primary);
            color: var(--primary-foreground);
        }

        .upload-text h3 {
            font-size: 1.125rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }

        .upload-text p {
            color: var(--muted-foreground);
            margin-bottom: 0.5rem;
        }

        .upload-formats {
            font-size: 0.75rem;
            color: var(--muted-foreground);
        }

        /* Image Preview */
        .image-preview {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            overflow: hidden;
            box-shadow: var(--shadow-medium);
            margin-bottom: 1.5rem;
        }

        .preview-image-container {
            position: relative;
        }

        .preview-image-container img {
            width: 100%;
            height: 16rem;
            object-fit: cover;
        }

        .btn-clear {
            position: absolute;
            top: 0.5rem;
            right: 0.5rem;
            width: 2rem;
            height: 2rem;
            padding: 0;
            border-radius: 50%;
            background: var(--destructive);
            color: var(--destructive-foreground);
        }

        .preview-info {
            padding: 1rem;
        }

        .file-info {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.875rem;
            color: var(--muted-foreground);
        }

        /* Process Section */
        .process-section {
            text-align: center;
        }

        /* Processing Section */
        .processing-section {
            max-width: 600px;
            margin: 0 auto;
        }

        .processing-card {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 2rem;
            text-align: center;
            box-shadow: var(--shadow-medium);
        }

        .processing-content {
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }

        .processing-spinner {
            position: relative;
            display: flex;
            justify-content: center;
        }

        .spinner {
            width: 48px;
            height: 48px;
            animation: spin 1s linear infinite;
            color: var(--primary);
        }

        .step-icon {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: var(--primary-foreground);
            width: 24px;
            height: 24px;
        }

        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }

        .processing-text h3 {
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }

        .processing-text p {
            color: var(--muted-foreground);
        }

        .processing-steps {
            display: flex;
            justify-content: center;
            gap: 2rem;
        }

        .step {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 0.5rem;
            color: var(--muted-foreground);
            transition: var(--transition-smooth);
        }

        .step.active {
            color: var(--primary);
        }

        .step-icon-small {
            background: var(--muted);
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: var(--transition-smooth);
        }

        .step.active .step-icon-small {
            background: hsl(var(--primary) / 0.1);
            color: var(--primary);
        }

        .step span {
            font-size: 0.875rem;
            font-weight: 500;
        }

        /* Results Section */
        .results-section {
            max-width: 800px;
            margin: 0 auto;
        }

        .results-header {
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 2rem;
        }

        .results-title h2 {
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 0.25rem;
        }

        .results-title p {
            color: var(--muted-foreground);
        }

        /* Result Card */
        .result-card {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 1.5rem;
            box-shadow: var(--shadow-medium);
            margin-bottom: 1.5rem;
        }

        .result-header {
            display: flex;
            align-items: flex-start;
            gap: 1rem;
        }

        .classification-icon {
            width: 48px;
            height: 48px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }

        .classification-icon.sensitive {
            background: hsl(var(--destructive) / 0.1);
            color: var(--destructive);
        }

        .classification-icon.non-sensitive {
            background: hsl(var(--success) / 0.1);
            color: var(--success);
        }

        .classification-content {
            flex: 1;
        }

        .classification-title {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 0.5rem;
        }

        .classification-title h3 {
            font-size: 1.25rem;
            font-weight: 600;
        }

        .classification-content p {
            color: var(--muted-foreground);
            margin-bottom: 0.75rem;
        }

        .confidence {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.875rem;
            color: var(--muted-foreground);
        }

        /* Processed Image Card */
        .processed-image-card {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            overflow: hidden;
            box-shadow: var(--shadow-medium);
        }

        .processed-image-container {
            position: relative;
            background: var(--muted);
        }

        .processed-image-container img {
            width: 100%;
            height: auto;
            max-height: 24rem;
            object-fit: contain;
        }

        .sensitive-overlay {
            position: absolute;
            top: 1rem;
            left: 1rem;
        }

        .sensitive-badge {
            background: hsl(var(--warning) / 0.9);
            color: var(--warning-foreground);
            padding: 0.25rem 0.75rem;
            border-radius: var(--radius);
            font-size: 0.75rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 0.25rem;
        }

        .processed-image-footer {
            background: hsl(var(--muted) / 0.3);
            border-top: 1px solid var(--border);
            padding: 1rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .processed-image-info h4 {
            font-weight: 600;
            margin-bottom: 0.25rem;
        }

        .processed-image-info p {
            font-size: 0.875rem;
            color: var(--muted-foreground);
        }

        /* Buttons */
        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            border-radius: var(--radius);
            font-size: 0.875rem;
            font-weight: 500;
            text-decoration: none;
            border: 1px solid transparent;
            cursor: pointer;
            transition: var(--transition-smooth);
            white-space: nowrap;
        }

        .btn:disabled {
            opacity: 0.5;
            pointer-events: none;
        }

        .btn-upload {
            background: var(--gradient-secondary);
            color: var(--secondary-foreground);
            border-color: var(--border);
            padding: 0.75rem 1.5rem;
        }

        .btn-upload:hover {
            background: var(--accent);
            color: var(--accent-foreground);
            box-shadow: var(--shadow-medium);
        }

        .btn-process {
            background: var(--gradient-primary);
            color: var(--primary-foreground);
            padding: 0.75rem 2rem;
            font-size: 1rem;
            box-shadow: var(--shadow-soft);
        }

        .btn-process:hover {
            box-shadow: var(--shadow-glow);
            transform: scale(1.05);
        }

        .btn-download {
            background: var(--success);
            color: var(--success-foreground);
            box-shadow: var(--shadow-soft);
        }

        .btn-download:hover {
            background: hsl(var(--success) / 0.9);
            box-shadow: var(--shadow-medium);
        }

        .btn-outline {
            background: transparent;
            color: var(--foreground);
            border-color: var(--border);
        }

        .btn-outline:hover {
            background: var(--accent);
            color: var(--accent-foreground);
        }

        .btn-clear {
            background: var(--destructive);
            color: var(--destructive-foreground);
        }

        .btn-clear:hover {
            background: hsl(var(--destructive) / 0.9);
        }

        /* Badges */
        .badge {
            display: inline-flex;
            align-items: center;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            border: 1px solid transparent;
        }

        .badge-destructive {
            background: hsl(var(--destructive) / 0.1);
            color: var(--destructive);
            border-color: hsl(var(--destructive) / 0.2);
        }

        .badge-success {
            background: hsl(var(--success) / 0.1);
            color: var(--success);
            border-color: hsl(var(--success) / 0.2);
        }

        /* Footer */
        .footer {
            background: hsl(var(--muted) / 0.3);
            border-top: 1px solid var(--border);
            margin-top: 4rem;
        }

        .footer .container {
            padding: 1.5rem 1rem;
            text-align: center;
        }

        .footer p {
            font-size: 0.875rem;
            color: var(--muted-foreground);
        }

        /* Toast Notification */
        .toast {
            position: fixed;
            top: 2rem;
            right: 2rem;
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 1rem;
            box-shadow: var(--shadow-large);
            z-index: 1000;
            max-width: 24rem;
            animation: slideIn 0.3s ease-out;
        }

        .toast-content {
            display: flex;
            align-items: flex-start;
            gap: 0.75rem;
        }

        .toast-icon {
            color: var(--success);
            flex-shrink: 0;
            margin-top: 0.125rem;
        }

        .toast-title {
            font-weight: 600;
            margin-bottom: 0.25rem;
        }

        .toast-description {
            font-size: 0.875rem;
            color: var(--muted-foreground);
        }

        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }

        /* Responsive Design */
        @media (max-width: 768px) {
            .container {
                padding: 0 0.5rem;
            }
            
            .main-container {
                padding: 1rem 0.5rem;
            }
            
            .features-grid {
                grid-template-columns: 1fr;
                gap: 1rem;
            }
            
            .upload-zone {
                padding: 1.5rem;
            }
            
            .upload-header h2 {
                font-size: 1.5rem;
            }
            
            .processing-steps {
                gap: 1rem;
            }
            
            .results-header {
                flex-direction: column;
                align-items: flex-start;
                gap: 0.5rem;
            }
            
            .processed-image-footer {
                flex-direction: column;
                align-items: flex-start;
                gap: 1rem;
            }
            
            .toast {
                right: 1rem;
                left: 1rem;
                max-width: none;
            }
        }
    </style>
</head>
<body>
    <!-- Header -->
    <header class="header">
        <div class="container">
            <div class="header-content">
                <div class="logo">
                    <div class="logo-icon">
                        <i data-lucide="shield"></i>
                    </div>
                    <div class="logo-text">
                        <h1>Document Privacy Scanner</h1>
                        <p>AI-powered sensitive information detection and protection</p>
                    </div>
                </div>
            </div>
        </div>
    </header>

    <main class="main-container">
        <!-- Upload Section -->
        <section id="upload-section" class="upload-section">
            <!-- Features -->
            <div class="features-grid">
                <div class="feature-card">
                    <div class="feature-icon">
                        <i data-lucide="file-text"></i>
                    </div>
                    <h3>Smart Detection</h3>
                    <p>Automatically identifies PAN cards, Aadhaar, tickets, bills and other sensitive documents</p>
                </div>
                
                <div class="feature-card">
                    <div class="feature-icon">
                        <i data-lucide="shield"></i>
                    </div>
                    <h3>Privacy Protection</h3>
                    <p>Automatically blurs sensitive information to protect your privacy</p>
                </div>
                
                <div class="feature-card">
                    <div class="feature-icon">
                        <i data-lucide="zap"></i>
                    </div>
                    <h3>Instant Results</h3>
                    <p>Get AI-powered analysis and protected images in seconds</p>
                </div>
            </div>

            <div class="separator"></div>

            <!-- Upload Area -->
            <div class="upload-content">
                <div class="upload-header">
                    <h2>Upload Your Document</h2>
                    <p>Select an image to scan for sensitive information</p>
                </div>

                <!-- Upload Zone -->
                <div id="upload-zone" class="upload-zone">
                    <div class="upload-zone-content">
                        <div id="upload-icon" class="upload-icon">
                            <i data-lucide="upload"></i>
                        </div>
                        
                        <div class="upload-text">
                            <h3 id="upload-title">Upload an image</h3>
                            <p id="upload-description">Drag and drop or click to select your PAN, Aadhaar, ticket, bill, or any document</p>
                            <p class="upload-formats">Supports JPEG, PNG, WebP • Max 10MB</p>
                        </div>

                        <button id="choose-file-btn" class="btn btn-upload">
                            <i data-lucide="upload"></i>
                            Choose File
                        </button>
                    </div>

                    <input type="file" id="file-input" accept="image/jpeg,image/jpg,image/png,image/webp" style="display: none;">
                </div>

                <!-- Image Preview -->
                <div id="image-preview" class="image-preview" style="display: none;">
                    <div class="preview-image-container">
                        <img id="preview-img" alt="Selected image preview">
                        <button id="clear-image-btn" class="btn btn-clear">
                            <i data-lucide="x"></i>
                        </button>
                    </div>
                    <div class="preview-info">
                        <div class="file-info">
                            <i data-lucide="file-image"></i>
                            <span id="file-name"></span>
                            <span id="file-size"></span>
                        </div>
                    </div>
                </div>

                <!-- Process Button -->
                <div id="process-section" class="process-section" style="display: none;">
                    <button id="process-btn" class="btn btn-process">
                        <i data-lucide="shield"></i>
                        Process Document
                    </button>
                </div>
            </div>
        </section>

        <!-- Processing Status -->
        <section id="processing-section" class="processing-section" style="display: none;">
            <div class="processing-card">
                <div class="processing-content">
                    <div class="processing-spinner">
                        <div class="spinner">
                            <i data-lucide="loader-2"></i>
                        </div>
                        <div id="processing-step-icon" class="step-icon">
                            <i data-lucide="image"></i>
                        </div>
                    </div>

                    <div class="processing-text">
                        <h3>Processing Your Image</h3>
                        <p id="processing-description">Reading document content</p>
                    </div>

                    <div class="processing-steps">
                        <div class="step active" data-step="0">
                            <div class="step-icon-small">
                                <i data-lucide="image"></i>
                            </div>
                            <span>Analyzing image</span>
                        </div>
                        <div class="step" data-step="1">
                            <div class="step-icon-small">
                                <i data-lucide="brain"></i>
                            </div>
                            <span>AI processing</span>
                        </div>
                        <div class="step" data-step="2">
                            <div class="step-icon-small">
                                <i data-lucide="shield"></i>
                            </div>
                            <span>Applying protection</span>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- Results Section -->
        <section id="results-section" class="results-section" style="display: none;">
            <div class="results-header">
                <button id="start-over-btn" class="btn btn-outline">
                    <i data-lucide="arrow-left"></i>
                    Process Another Document
                </button>
                <div class="results-title">
                    <h2>Processing Complete</h2>
                    <p>Your document has been analyzed and protected</p>
                </div>
            </div>

            <!-- Classification Result -->
            <div class="result-card">
                <div class="result-header">
                    <div id="classification-icon" class="classification-icon">
                        <i data-lucide="alert-triangle"></i>
                    </div>
                    
                    <div class="classification-content">
                        <div class="classification-title">
                            <h3>Classification Result</h3>
                            <span id="classification-badge" class="badge badge-destructive">Sensitive</span>
                        </div>
                        
                        <p id="classification-description">
                            This document contains sensitive information and has been automatically blurred for privacy protection.
                        </p>
                        
                        <div id="confidence-display" class="confidence">
                            <i data-lucide="shield"></i>
                            <span>Confidence: <span id="confidence-value">85</span>%</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Processed Image -->
            <div class="processed-image-card">
                <div class="processed-image-container">
                    <img id="processed-img" alt="Processed document">
                    <div id="sensitive-overlay" class="sensitive-overlay" style="display: none;">
                        <span class="sensitive-badge">
                            <i data-lucide="shield"></i>
                            Sensitive Content Blurred
                        </span>
                    </div>
                </div>
                
                <div class="processed-image-footer">
                    <div class="processed-image-info">
                        <h4>Processed Image</h4>
                        <p id="processed-status">Privacy protected</p>
                    </div>
                    
                    <button id="download-btn" class="btn btn-download">
                        <i data-lucide="download"></i>
                        Download
                    </button>
                </div>
            </div>
        </section>
    </main>

    <!-- Footer -->
    <footer class="footer">
        <div class="container">
            <p>Powered by AI • Your privacy is our priority • Documents are processed securely</p>
        </div>
    </footer>

    <!-- Toast Notification -->
    <div id="toast" class="toast" style="display: none;">
        <div class="toast-content">
            <div class="toast-icon">
                <i data-lucide="check-circle"></i>
            </div>
            <div class="toast-text">
                <div class="toast-title"></div>
                <div class="toast-description"></div>
            </div>
        </div>
    </div>

    <!-- JavaScript Inlined -->
    <script>
        // Document Privacy Scanner - JavaScript

        class DocumentScanner {
            constructor() {
                this.selectedFile = null;
                this.isProcessing = false;
                this.processingSteps = [
                    { icon: 'image', label: 'Analyzing image', description: 'Reading document content' },
                    { icon: 'brain', label: 'AI processing', description: 'Detecting sensitive information' },
                    { icon: 'shield', label: 'Applying protection', description: 'Securing sensitive data' }
                ];
                this.currentStep = 0;
                this.processingInterval = null;
                this.originalFileName = '';
                this.processedImageUrl = '';

                this.init();
            }

            init() {
                this.bindEvents();
                this.setupDragAndDrop();
            }

            bindEvents() {
                // File input
                const fileInput = document.getElementById('file-input');
                const chooseFileBtn = document.getElementById('choose-file-btn');
                const uploadZone = document.getElementById('upload-zone');

                fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
                chooseFileBtn.addEventListener('click', () => fileInput.click());
                uploadZone.addEventListener('click', (e) => {
                    // Prevent file click if it's the clear button being clicked
                    if (e.target.closest('#choose-file-btn')) return;
                    fileInput.click();
                });

                // Clear image
                const clearImageBtn = document.getElementById('clear-image-btn');
                clearImageBtn.addEventListener('click', () => this.clearImage());

                // Process button
                const processBtn = document.getElementById('process-btn');
                processBtn.addEventListener('click', () => this.processImage());

                // Start over button
                const startOverBtn = document.getElementById('start-over-btn');
                startOverBtn.addEventListener('click', () => this.startOver());

                // Download button
                const downloadBtn = document.getElementById('download-btn');
                downloadBtn.addEventListener('click', () => this.downloadImage());
            }

            setupDragAndDrop() {
                const uploadZone = document.getElementById('upload-zone');

                uploadZone.addEventListener('dragover', (e) => {
                    e.preventDefault();
                    uploadZone.classList.add('drag-over');
                    document.getElementById('upload-title').textContent = 'Drop your image here';
                });

                uploadZone.addEventListener('dragleave', (e) => {
                    e.preventDefault();
                    // Check if the relatedTarget is outside the upload zone before removing drag-over class
                    if (e.relatedTarget === null || !uploadZone.contains(e.relatedTarget)) {
                        uploadZone.classList.remove('drag-over');
                        document.getElementById('upload-title').textContent = 'Upload an image';
                    }
                });

                uploadZone.addEventListener('drop', (e) => {
                    e.preventDefault();
                    uploadZone.classList.remove('drag-over');
                    document.getElementById('upload-title').textContent = 'Upload an image';

                    const files = e.dataTransfer.files;
                    if (files.length > 0) {
                        this.handleFile(files[0]);
                    }
                });
            }

            handleFileSelect(event) {
                const file = event.target.files[0];
                if (file) {
                    this.handleFile(file);
                }
            }

            handleFile(file) {
                const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
                
                if (!validTypes.includes(file.type)) {
                    this.showToast('Invalid file type', 'Please select a JPEG, PNG, or WebP image file.', 'error');
                    return;
                }

                if (file.size > 10 * 1024 * 1024) { // 10MB limit
                    this.showToast('File too large', 'Please select an image smaller than 10MB.', 'error');
                    return;
                }

                this.selectedFile = file;
                this.showImagePreview(file);
            }

            showImagePreview(file) {
                const uploadZone = document.getElementById('upload-zone');
                const imagePreview = document.getElementById('image-preview');
                const processSection = document.getElementById('process-section');
                const previewImg = document.getElementById('preview-img');
                const fileName = document.getElementById('file-name');
                const fileSize = document.getElementById('file-size');

                // Hide upload zone
                uploadZone.style.display = 'none';

                // Create and show preview
                const reader = new FileReader();
                reader.onload = (e) => {
                    previewImg.src = e.target.result;
                };
                reader.readAsDataURL(file);

                fileName.textContent = file.name;
                fileSize.textContent = `(${(file.size / 1024 / 1024).toFixed(2)} MB)`;

                // Show preview and process section
                imagePreview.style.display = 'block';
                processSection.style.display = 'block';
            }

            clearImage() {
                this.selectedFile = null;
                
                // Reset UI
                document.getElementById('upload-zone').style.display = 'block';
                document.getElementById('image-preview').style.display = 'none';
                document.getElementById('process-section').style.display = 'none';
                document.getElementById('file-input').value = '';
                this.processedImageUrl = '';
                this.originalFileName = '';

                // Hide results if visible
                document.getElementById('results-section').style.display = 'none';
                document.getElementById('upload-section').style.display = 'block';
            }

            async processImage() {
                if (!this.selectedFile || this.isProcessing) return;

                this.isProcessing = true;
                this.showProcessingStatus();

                try {
                    // Create FormData to send to Flask backend
                    const formData = new FormData();
                    formData.append('file', this.selectedFile);

                    // Start processing animation
                    this.startProcessingAnimation();

                    // Send to Flask backend
                    const response = await fetch('/upload', {
                        method: 'POST',
                        body: formData,
                    });

                    // Stop processing animation regardless of success/failure
                    if (this.processingInterval) {
                        clearInterval(this.processingInterval);
                        this.processingInterval = null;
                    }

                    if (!response.ok) {
                        // Check if the response contains a JSON error message
                        try {
                            const errorData = await response.json();
                            throw new Error(errorData.error || `Server responded with status ${response.status}`);
                        } catch (e) {
                            // If not JSON, use the status text
                            throw new Error(`Server responded with status ${response.statusText}`);
                        }
                    }

                    const data = await response.json();
                    
                    // Show results
                    this.showResults({
                        classification: data.classification,
                        processedImageUrl: data.processed_image_url, // Base64 Data URL
                        confidence: data.confidence,
                        originalFileName: this.selectedFile.name
                    });

                    this.showToast('Processing complete', `Document classified as ${data.classification}`);

                } catch (error) {
                    console.error('Processing error:', error);
                    
                    // Fallback for error handling
                    this.showToast('Processing failed', `Server error: ${error.message || 'Check console.'}`, 'error');

                    // Stop processing animation if still running
                    if (this.processingInterval) {
                        clearInterval(this.processingInterval);
                        this.processingInterval = null;
                    }
                    
                    // Go back to upload state
                    this.clearImage(); 
                }

                this.isProcessing = false;
            }

            showProcessingStatus() {
                document.getElementById('upload-section').style.display = 'none';
                document.getElementById('processing-section').style.display = 'block';
            }

            startProcessingAnimation() {
                this.currentStep = 0;
                this.updateProcessingStep();
                
                this.processingInterval = setInterval(() => {
                    // Increment step until max (3 steps, 0-2)
                    if (this.currentStep < this.processingSteps.length - 1) {
                         this.currentStep++;
                    } else {
                        // Cycle the last step to indicate continuous processing
                        this.currentStep = this.processingSteps.length - 1; 
                    }
                    this.updateProcessingStep();
                }, 1500);
            }

            updateProcessingStep() {
                const steps = document.querySelectorAll('.step');
                const stepIcon = document.getElementById('processing-step-icon');
                const description = document.getElementById('processing-description');

                // Update active step
                steps.forEach((step, index) => {
                    if (index === this.currentStep) {
                        step.classList.add('active');
                    } else {
                        step.classList.remove('active');
                    }
                });

                // Update icon and description
                const currentStepData = this.processingSteps[this.currentStep];
                stepIcon.innerHTML = `<i data-lucide="${currentStepData.icon}"></i>`;
                description.textContent = currentStepData.description;

                // Re-initialize icons
                if (window.lucide) {
                    lucide.createIcons();
                }
            }

            showResults(result) {
                // Stop processing animation
                if (this.processingInterval) {
                    clearInterval(this.processingInterval);
                    this.processingInterval = null;
                }

                // Hide processing section
                document.getElementById('processing-section').style.display = 'none';

                // Update results
                this.updateClassificationResult(result);
                this.updateProcessedImage(result);

                // Show results section
                document.getElementById('results-section').style.display = 'block';
            }

            updateClassificationResult(result) {
                const isSensitive = result.classification === 'Sensitive';
                
                // Update icon
                const classificationIcon = document.getElementById('classification-icon');
                classificationIcon.className = `classification-icon ${isSensitive ? 'sensitive' : 'non-sensitive'}`;
                classificationIcon.innerHTML = isSensitive ? 
                    '<i data-lucide="alert-triangle"></i>' : 
                    '<i data-lucide="check-circle"></i>';

                // Update badge
                const badge = document.getElementById('classification-badge');
                badge.className = `badge ${isSensitive ? 'badge-destructive' : 'badge-success'}`;
                badge.textContent = result.classification;

                // Update description
                const description = document.getElementById('classification-description');
                description.textContent = isSensitive ?
                    'This document contains sensitive information and has been automatically blurred for privacy protection.' :
                    'This document does not contain sensitive information and is safe to share.';

                // Update confidence
                if (result.confidence) {
                    document.getElementById('confidence-value').textContent = Math.round(result.confidence * 100);
                } else {
                    document.getElementById('confidence-value').textContent = 'N/A';
                }

                // Re-initialize icons
                if (window.lucide) {
                    lucide.createIcons();
                }
            }

            updateProcessedImage(result) {
                const processedImg = document.getElementById('processed-img');
                const sensitiveOverlay = document.getElementById('sensitive-overlay');
                const processedStatus = document.getElementById('processed-status');

                processedImg.src = result.processedImageUrl;
                processedImg.alt = `Processed ${result.classification.toLowerCase()} document`;

                const isSensitive = result.classification === 'Sensitive';
                sensitiveOverlay.style.display = isSensitive ? 'block' : 'none';
                processedStatus.textContent = isSensitive ? 'Privacy protected' : 'Original quality maintained';

                // Store for download
                this.processedImageUrl = result.processedImageUrl;
                this.originalFileName = result.originalFileName;
            }

            startOver() {
                // Stop any processing
                if (this.processingInterval) {
                    clearInterval(this.processingInterval);
                    this.processingInterval = null;
                }

                this.isProcessing = false;
                this.clearImage();
            }

            downloadImage() {
                if (!this.processedImageUrl || !this.originalFileName) return;

                // Create download link
                const link = document.createElement('a');
                link.href = this.processedImageUrl;
                
                // Ensure file extension is included, default to .png if necessary
                const parts = this.originalFileName.split('.');
                const extension = parts.length > 1 ? parts.pop() : 'png';

                link.download = `processed_${parts.join('.')}.${extension}`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);

                this.showToast('Download started', 'Your processed image is being downloaded.');
            }

            showToast(title, description, type = 'success') {
                const toast = document.getElementById('toast');
                const toastIcon = toast.querySelector('.toast-icon i');
                const toastTitle = toast.querySelector('.toast-title');
                const toastDescription = toast.querySelector('.toast-description');
                const iconContainer = toast.querySelector('.toast-icon');

                // Update content
                toastTitle.textContent = title;
                toastDescription.textContent = description;

                // Update icon based on type
                if (type === 'error') {
                    toastIcon.setAttribute('data-lucide', 'alert-circle');
                    iconContainer.style.color = 'var(--destructive)';
                } else {
                    toastIcon.setAttribute('data-lucide', 'check-circle');
                    iconContainer.style.color = 'var(--success)';
                }

                // Show toast
                toast.style.display = 'block';

                // Re-initialize icons
                if (window.lucide) {
                    lucide.createIcons();
                }

                // Hide after 5 seconds
                setTimeout(() => {
                    toast.style.display = 'none';
                }, 5000);
            }
        }

        // Initialize when DOM is loaded
        document.addEventListener('DOMContentLoaded', () => {
            new DocumentScanner();
            // Initialize Lucide icons on DOM load
            if (window.lucide) {
                lucide.createIcons();
            }
        });
    </script>
</body>
</html>
"""

# -------------------------------
# Routes
# -------------------------------
@app.route('/')
def home():
    """Serves the single-page HTML/CSS/JS frontend."""
    # Note: Using render_template_string instead of a separate file 
    # to keep the solution contained, matching the previous FastAPI structure.
    return render_template_string(HTML_CONTENT)

@app.route('/upload', methods=['POST'])
def upload_file():
    """
    Handles file upload, runs ML processing, and returns JSON response 
    expected by the frontend JavaScript.
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file part in request"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    # 1. Save uploaded file to a temporary location
    temp_input_file = None
    temp_output_file = None
    
    try:
        # Use NamedTemporaryFile to safely handle file storage
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as tmp:
            file.save(tmp.name)
            temp_input_file = tmp.name
        
        # 2. Run Prediction (Classification)
        classification_label, confidence_score = predict_image(temp_input_file)
        
        # 3. Determine the final image path
        if classification_label == "Sensitive":
            # If Sensitive, run Redaction (OCR + Blurring)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_out:
                temp_output_file = tmp_out.name
            
            # The redact function saves the processed image to temp_output_file
            redact_sensitive_info(temp_input_file, temp_output_file)
            final_image_path = temp_output_file
            # Force output to PNG for consistency after CV processing
            output_format = "PNG" 
        else:
            # If Non-sensitive, use the original image
            final_image_path = temp_input_file
            # Determine format from original file extension
            output_format = file.filename.split('.')[-1].upper()
        
        # 4. Read the final image bytes and encode to Base64 (Data URL format)
        with open(final_image_path, "rb") as f:
            image_bytes = f.read()
            
        img_str = base64.b64encode(image_bytes).decode()
        processed_data_url = f"data:image/{output_format.lower()};base64,{img_str}"

        # 5. Return Results to Front-end as JSON
        return jsonify({
            "classification": classification_label,
            "confidence": confidence_score,
            "processed_image_url": processed_data_url,
        })

    except Exception as e:
        print(f"Server-side error during processing: {e}")
        return jsonify({"error": f"An internal error occurred: {str(e)}"}), 500
        
    finally:
        # 6. CRITICAL: Cleanup temporary files
        if temp_input_file and os.path.exists(temp_input_file):
            os.remove(temp_input_file)
        if temp_output_file and os.path.exists(temp_output_file):
            os.remove(temp_output_file)

# The /uploads and /outputs routes are no longer needed since we return Base64 Data URLs.

# -------------------------------
if __name__ == "__main__":
    # Ensure you have Flask, torch, torchvision, opencv-python, and paddleocr installed
    app.run(debug=True)
