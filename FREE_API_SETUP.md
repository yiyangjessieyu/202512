# Free AI API Alternatives Setup Guide

This guide shows you how to set up free alternatives to OpenAI's paid API for the Instagram Content Analyzer.

## Option 1: Completely Free (Local Analysis)

### What you get:
- ✅ Basic object detection with OpenCV
- ✅ Text extraction with Tesseract OCR
- ✅ Color and brightness analysis
- ✅ No API costs ever
- ❌ Less sophisticated than AI models

### Setup:
```bash
# Install Tesseract OCR for text extraction
brew install tesseract  # macOS
# or
sudo apt-get install tesseract-ocr  # Ubuntu

# Install Python OCR library
pip install pytesseract

# Test with your video
python examples/free_video_analysis_demo.py "examples/videos/MVI_7526.MP4"
```

## Option 2: Hugging Face (Best Free AI)

### What you get:
- ✅ 1,000 free API requests/month
- ✅ Advanced AI models (CLIP, BLIP, etc.)
- ✅ Image and text analysis
- ✅ No credit card required
- ❌ Rate limits

### Setup:
1. Go to [huggingface.co](https://huggingface.co) and create account
2. Get API key at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
3. Add to your `.env` file:
```bash
HUGGINGFACE_API_KEY=hf_your_token_here
```

### Usage:
```python
from transformers import pipeline

# Image analysis
classifier = pipeline("image-classification")
result = classifier("path/to/image.jpg")

# Text analysis
sentiment = pipeline("sentiment-analysis")
result = sentiment("This is amazing!")
```

## Option 3: Google AI Studio (Gemini)

### What you get:
- ✅ 15 requests/minute, 1,500/day free
- ✅ Gemini Pro Vision (video analysis)
- ✅ Very capable AI model
- ❌ Requires Google account

### Setup:
1. Go to [aistudio.google.com](https://aistudio.google.com)
2. Create API key
3. Add to `.env`:
```bash
GOOGLE_AI_API_KEY=your_key_here
```

## Option 4: Local AI with Ollama (Advanced)

### What you get:
- ✅ Completely free and private
- ✅ Run Llama, Mistral, etc. locally
- ✅ No internet required after setup
- ❌ Requires powerful computer
- ❌ Large downloads (4GB+ models)

### Setup:
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Download a model
ollama pull llama2

# Use in Python
pip install ollama
```

## Recommended Approach

**For testing/learning**: Use the free local analysis (Option 1)
**For production**: Start with Hugging Face free tier (Option 2)
**For heavy usage**: Consider Google AI Studio (Option 3)

## Cost Comparison

| Service | Free Tier | Paid Tier | Best For |
|---------|-----------|-----------|----------|
| Local/OpenCV | Unlimited | N/A | Basic analysis |
| Hugging Face | 1,000 req/month | $9/month | AI analysis |
| Google Gemini | 1,500 req/day | Pay per use | Video analysis |
| OpenAI GPT-4V | $5 minimum | $0.01-0.04/image | Best quality |

## Quick Test Commands

```bash
# Test free local analysis
python examples/free_video_analysis_demo.py "your_video.mp4"

# Test with OpenCV only (no OCR)
python examples/simple_video_demo.py "your_video.mp4"

# Test with any API key (OpenAI, Hugging Face, etc.)
python examples/video_processor_demo.py --video "your_video.mp4"
```

## Next Steps

1. **Start with free local analysis** to understand the system
2. **Try Hugging Face** for better AI analysis
3. **Upgrade to paid APIs** only when you need production quality

The Instagram Content Analyzer works with all these options - just change the API configuration in your `.env` file!