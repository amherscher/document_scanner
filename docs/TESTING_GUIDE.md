# Testing Your Trained Model - Step by Step

## After Training: What's Next?

Once you've trained your model, follow these steps to test it with real scanned invoices.

## Step 1: Verify Model Was Created

Check that your model checkpoint exists:

```bash
ls -lh ml_pipeline/checkpoints/best_model.pt
```

You should see the model file. If it doesn't exist, check `ml_pipeline/checkpoints/final_model.pt`.

## Step 2: Set Model Path (if needed)

The Flask app automatically looks for the model at:
```
ml_pipeline/checkpoints/best_model.pt
```

If your model is in a different location, set the environment variable:

```bash
export INVOICE_MODEL_PATH=/path/to/your/best_model.pt
```

Or edit `app.py` line 25 to change the default path.

## Step 3: Start the Flask App

```bash
python app.py
```

You should see output like:
```
Loaded invoice classification model from /path/to/best_model.pt
 * Running on http://0.0.0.0:5000
```

If you see "Model not found", check Step 2.

## Step 4: Open Web Interface

1. **On the same machine**: Open `http://localhost:5000`
2. **From another device on network**: Open `http://YOUR_SERVER_IP:5000`
3. **From Raspberry Pi**: If running on Pi, use `http://pi-scan.local:5000` (if mDNS is set up)

## Step 5: Check ML Status

Look at the web page - you should see a status indicator:
- ✅ **Green**: "ML Model Ready" - Model is loaded and ready
- ⚠️ **Yellow**: "Model not found" or "Model failed to load"

You can also check via API:
```bash
curl http://localhost:5000/api/ml/status
```

## Step 6: Test with a Scan

### Option A: Scan a Real Invoice (Recommended)

1. **Place an invoice** on the scanner bed (or in front of camera)
2. **Click "Scan"** button in the web interface
3. **Wait for scan** to complete (camera captures image)
4. **Classification happens automatically** - you'll see:
   - Predicted expense category
   - Confidence score
   - Top 3 predictions
   - Whether text was extracted

### Option B: Test with Existing File

If you have a scanned invoice file already:

1. **Upload or place** the file in the `scans/` directory
2. **Refresh** the page to see it in "Recent files"
3. **Click "Classify"** button next to the file
4. **See classification results**

## Step 7: Verify Results

Check that:
- ✅ Category is predicted (not "Other" unless appropriate)
- ✅ Confidence is reasonable (>0.5 for good predictions)
- ✅ Text was extracted (if using text/hybrid model)
- ✅ Results make sense for the invoice type

## Troubleshooting

### Model Not Loading

**Problem**: Status shows "Model not found" or "Model failed to load"

**Solutions**:
1. Check model path: `ls ml_pipeline/checkpoints/best_model.pt`
2. Verify model was trained successfully
3. Check Flask app logs for error messages
4. Ensure PyTorch and transformers are installed

### No Classification Results

**Problem**: Scan completes but no category shown

**Solutions**:
1. Check ML status: Is model loaded?
2. Check OCR: Is text being extracted? (Look for "Text extracted" message)
3. For text models: Ensure OCR is working (`tesseract --version`)
4. Check Flask app console for errors

### Low Confidence / Wrong Categories

**Problem**: Predictions are wrong or confidence is low

**Solutions**:
1. **Train longer**: More epochs might help
2. **More data**: Train with more examples per category
3. **Better data**: Ensure training data matches real invoices
4. **Check categories**: Verify your invoice categories match training categories

### OCR Not Working

**Problem**: "No text extracted" message

**Solutions**:
```bash
# Install Tesseract
sudo apt-get install -y tesseract-ocr

# Verify installation
tesseract --version

# Install Python package
pip install pytesseract
```

## Testing Checklist

- [ ] Model file exists (`best_model.pt` or `final_model.pt`)
- [ ] Flask app starts without errors
- [ ] ML status shows "Model Ready"
- [ ] Can scan an invoice
- [ ] Classification results appear
- [ ] Category prediction makes sense
- [ ] Confidence score is reasonable
- [ ] Text extraction works (for text/hybrid models)

## Quick Test Commands

### Test Model Loading
```bash
python -c "
from ml_pipeline.inference import InvoiceCategorizer
c = InvoiceCategorizer('ml_pipeline/checkpoints/best_model.pt')
print(f'Model loaded! Categories: {c.categories}')
"
```

### Test Classification (Command Line)
```bash
python ml_pipeline/inference.py \
    --checkpoint ml_pipeline/checkpoints/best_model.pt \
    --text "Invoice for office supplies including pens and paper" \
    --probs
```

### Test with Image
```bash
python ml_pipeline/inference.py \
    --checkpoint ml_pipeline/checkpoints/best_model.pt \
    --image scans/scan_20240120_143022.jpg \
    --probs
```

## Next Steps After Testing

Once it's working:

1. **Improve accuracy**: 
   - Train with more data
   - Fine-tune hyperparameters
   - Add more categories

2. **Deploy for production**:
   - Set up as a systemd service
   - Add authentication
   - Set up HTTPS

3. **Integrate with other systems**:
   - Connect to accounting software
   - Save to database
   - Send notifications

4. **Monitor performance**:
   - Track accuracy over time
   - Collect feedback
   - Retrain with new data

## Example Workflow

```
1. Train model → best_model.pt created
2. Start Flask app → Model loads automatically
3. Open web interface → See "ML Model Ready" status
4. Scan invoice → Camera captures image
5. OCR extracts text → Text shown in results
6. Model classifies → Category + confidence displayed
7. Review results → Verify accuracy
8. Save/export → Use categorized invoice
```

That's it! Your model should now be working with the scanner. 🎉

