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
        uploadZone.addEventListener('click', () => fileInput.click());

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
            if (!uploadZone.contains(e.relatedTarget)) {
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

            if (!response.ok) {
                throw new Error('Processing failed');
            }

            const data = await response.json();
            
            // Show results
            this.showResults({
                classification: data.classification,
                processedImageUrl: data.processed_image_url,
                confidence: data.confidence,
                originalFileName: this.selectedFile.name
            });

            this.showToast('Processing complete', `Document classified as ${data.classification}`);

        } catch (error) {
            console.log('Using demo mode due to error:', error.message);
            
            // Demo mode - simulate processing
            setTimeout(() => {
                const mockResult = {
                    classification: Math.random() > 0.5 ? 'Sensitive' : 'Non-Sensitive',
                    processedImageUrl: URL.createObjectURL(this.selectedFile),
                    confidence: 0.85 + Math.random() * 0.15,
                    originalFileName: this.selectedFile.name
                };
                
                this.showResults(mockResult);
                this.showToast('Processing complete (Demo)', `Document classified as ${mockResult.classification}`);
            }, 3000);
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
            this.currentStep = (this.currentStep + 1) % this.processingSteps.length;
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
        link.download = `processed_${this.originalFileName}`;
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

        // Update content
        toastTitle.textContent = title;
        toastDescription.textContent = description;

        // Update icon based on type
        if (type === 'error') {
            toastIcon.setAttribute('data-lucide', 'alert-circle');
            toast.querySelector('.toast-icon').style.color = 'var(--destructive)';
        } else {
            toastIcon.setAttribute('data-lucide', 'check-circle');
            toast.querySelector('.toast-icon').style.color = 'var(--success)';
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
});