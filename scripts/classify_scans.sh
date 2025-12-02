#!/bin/bash
# Classify all scans on the server

SCANS_DIR=${SCANS_DIR:-/home/data/Purdue/pi/scans}
MODEL_PATH=${MODEL_PATH:-/home/data/Purdue/pi/checkpoints/best_model.pt}

echo "Classifying all scans..."
echo "Scans directory: $SCANS_DIR"
echo "Model path: $MODEL_PATH"
echo ""

cd /home/data/Purdue/pi

# Check if model exists
if [ ! -f "$MODEL_PATH" ]; then
    echo "Error: Model not found at $MODEL_PATH"
    exit 1
fi

# Check if scans directory exists
if [ ! -d "$SCANS_DIR" ]; then
    echo "Error: Scans directory not found: $SCANS_DIR"
    exit 1
fi

# Count files
FILE_COUNT=$(find "$SCANS_DIR" -type f \( -name "*.jpg" -o -name "*.jpeg" -o -name "*.png" -o -name "*.pdf" \) | wc -l)
echo "Found $FILE_COUNT files to classify"
echo ""

# Run classification
python3 scripts/classify_all_scans.py --scans_dir "$SCANS_DIR" --model_path "$MODEL_PATH"

echo ""
echo "✅ Done! Check expenses.csv in $SCANS_DIR"

