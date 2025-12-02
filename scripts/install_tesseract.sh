#!/bin/bash
# Install tesseract OCR for text extraction

echo "Installing Tesseract OCR..."

if command -v apt-get &> /dev/null; then
    sudo apt-get update
    sudo apt-get install -y tesseract-ocr
elif command -v yum &> /dev/null; then
    sudo yum install -y tesseract
elif command -v brew &> /dev/null; then
    brew install tesseract
else
    echo "Error: Package manager not found. Please install tesseract manually."
    exit 1
fi

echo "Tesseract installed. Testing..."
tesseract --version

echo ""
echo "✅ Tesseract OCR is now installed!"
echo "You can now extract text and amounts from invoice images."

