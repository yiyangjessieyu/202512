#!/usr/bin/env python3
"""
Free Video Analysis Demo using local/free alternatives.

This demo shows how to analyze videos without paid APIs using:
1. OpenCV for basic computer vision
2. Tesseract OCR for text extraction
3. Local image analysis
"""

import sys
import os
import cv2
import numpy as np
from pathlib import Path

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.models.content import VideoFile


def extract_text_with_ocr(image):
    """
    Extract text from image using Tesseract OCR (free).
    
    Args:
        image: OpenCV image
        
    Returns:
        List of detected text strings
    """
    try:
        import pytesseract
        
        # Convert to grayscale for better OCR
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply threshold to get better text detection
        _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        
        # Extract text
        text = pytesseract.image_to_string(thresh)
        
        # Clean and filter text
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        return lines
        
    except ImportError:
        print("Note: Install pytesseract for OCR text extraction: pip install pytesseract")
        return []
    except Exception as e:
        print(f"OCR error: {e}")
        return []


def detect_objects_with_opencv(image):
    """
    Detect basic objects using OpenCV (completely free).
    
    Args:
        image: OpenCV image
        
    Returns:
        List of detected objects/features
    """
    objects = []
    
    # Convert to different color spaces for analysis
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    # Detect edges
    edges = cv2.Canny(gray, 50, 150)
    edge_count = np.sum(edges > 0)
    
    if edge_count > 10000:
        objects.append("complex_scene")
    elif edge_count > 5000:
        objects.append("moderate_detail")
    else:
        objects.append("simple_scene")
    
    # Detect contours (shapes)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    large_contours = [c for c in contours if cv2.contourArea(c) > 1000]
    
    if len(large_contours) > 10:
        objects.append("many_objects")
    elif len(large_contours) > 5:
        objects.append("several_objects")
    elif len(large_contours) > 0:
        objects.append("few_objects")
    
    # Analyze colors
    mean_color = np.mean(image, axis=(0, 1))
    
    if mean_color[2] > 150:  # High red
        objects.append("red_dominant")
    if mean_color[1] > 150:  # High green
        objects.append("green_dominant")
    if mean_color[0] > 150:  # High blue
        objects.append("blue_dominant")
    
    # Check brightness
    brightness = np.mean(gray)
    if brightness > 200:
        objects.append("bright_scene")
    elif brightness < 50:
        objects.append("dark_scene")
    else:
        objects.append("normal_lighting")
    
    return objects


def analyze_video_free(video_path: str):
    """
    Analyze video using completely free methods.
    
    Args:
        video_path: Path to video file
    """
    if not os.path.exists(video_path):
        print(f"Error: Video file not found: {video_path}")
        return
    
    print(f"=== Free Video Analysis: {os.path.basename(video_path)} ===\n")
    
    # Open video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Error: Could not open video file")
        return
    
    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration = frame_count / fps if fps > 0 else 0
    
    print(f"Video Properties:")
    print(f"  Duration: {duration:.2f} seconds")
    print(f"  FPS: {fps:.2f}")
    print(f"  Resolution: {width}x{height}")
    print(f"  Total Frames: {frame_count}")
    
    # Analyze frames at intervals
    analysis_frames = 5
    frame_interval = max(1, frame_count // analysis_frames)
    
    all_objects = []
    all_text = []
    
    print(f"\nAnalyzing {analysis_frames} frames...")
    
    for i in range(analysis_frames):
        frame_number = i * frame_interval
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        
        ret, frame = cap.read()
        if not ret:
            break
        
        timestamp = frame_number / fps
        print(f"  Frame {i+1}: {timestamp:.2f}s")
        
        # Detect objects with OpenCV
        objects = detect_objects_with_opencv(frame)
        all_objects.extend(objects)
        print(f"    Objects: {objects}")
        
        # Extract text with OCR
        text_lines = extract_text_with_ocr(frame)
        if text_lines:
            all_text.extend(text_lines)
            print(f"    Text: {text_lines[:2]}...")  # Show first 2 lines
        else:
            print(f"    Text: None detected")
    
    cap.release()
    
    # Aggregate results
    unique_objects = list(set(all_objects))
    unique_text = list(set(all_text))
    
    print(f"\n=== Analysis Results ===")
    print(f"Detected Features: {unique_objects}")
    print(f"Extracted Text Lines: {len(unique_text)}")
    
    if unique_text:
        print(f"Sample Text:")
        for text in unique_text[:5]:  # Show first 5 unique text lines
            print(f"  - {text}")
    
    print(f"\n=== Free Analysis Complete ===")
    print(f"This analysis used only free, local tools:")
    print(f"- OpenCV for computer vision")
    print(f"- Tesseract OCR for text extraction")
    print(f"- No API calls or costs involved")


def main():
    """Main function."""
    if len(sys.argv) != 2:
        print("Usage: python examples/free_video_analysis_demo.py /path/to/video.mp4")
        print("\nThis demo uses completely free tools:")
        print("- OpenCV (already installed)")
        print("- Tesseract OCR (install with: brew install tesseract)")
        print("- No API keys required!")
        sys.exit(1)
    
    video_path = sys.argv[1]
    analyze_video_free(video_path)


if __name__ == "__main__":
    main()