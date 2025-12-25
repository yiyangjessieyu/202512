#!/usr/bin/env python3
"""
Simple VideoProcessor demo for testing with local MP4 files.

Usage:
    python examples/simple_video_demo.py /path/to/your/video.mp4
"""

import sys
import os
import cv2

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.analysis.video_processor import VideoProcessor
from src.models.content import VideoFile


def analyze_video_file(video_path: str):
    """
    Analyze a video file using the VideoProcessor.
    
    Args:
        video_path: Path to the MP4 video file
    """
    if not os.path.exists(video_path):
        print(f"Error: Video file not found: {video_path}")
        return
    
    print(f"=== Analyzing Video: {os.path.basename(video_path)} ===\n")
    
    # Get video information using OpenCV
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video file")
        return
    
    # Extract video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration = frame_count / fps if fps > 0 else 0
    file_size = os.path.getsize(video_path)
    
    cap.release()
    
    print(f"Video Properties:")
    print(f"  File: {video_path}")
    print(f"  Size: {file_size / (1024*1024):.2f} MB")
    print(f"  Duration: {duration:.2f} seconds")
    print(f"  FPS: {fps:.2f}")
    print(f"  Resolution: {width}x{height}")
    print(f"  Total Frames: {frame_count}")
    
    # Create VideoFile object
    video_file = VideoFile(
        file_path=video_path,
        duration=duration,
        fps=int(fps),
        resolution=(width, height)
    )
    
    # Initialize VideoProcessor
    processor = VideoProcessor()
    
    print(f"\nExtracting frames...")
    
    try:
        # Extract frames (limit to 5 for demo)
        frames = processor.extract_frames(video_file, max_frames=5)
        
        print(f"Successfully extracted {len(frames)} frames:")
        for i, frame in enumerate(frames):
            print(f"  Frame {i+1}: timestamp={frame.timestamp:.2f}s, "
                  f"resolution={frame.resolution[0]}x{frame.resolution[1]}")
        
        print(f"\nFrame Analysis:")
        print("Note: This demo shows frame extraction without OpenAI API calls.")
        print("To enable full analysis with GPT-4V:")
        print("1. Set your OpenAI API key in the .env file")
        print("2. The processor will analyze each frame for:")
        print("   - Objects and items visible")
        print("   - Text overlays and readable text")
        print("   - Scene descriptions and context")
        print("   - People and activities")
        print("   - Brands and commercial elements")
        
        # Clean up temporary frame files
        processor.cleanup_temp_files(frames)
        print(f"\nTemporary frame files cleaned up.")
        
        print(f"\n=== Analysis Complete ===")
        
    except Exception as e:
        print(f"Error during frame extraction: {str(e)}")
        print("This might be due to:")
        print("- Unsupported video format")
        print("- Corrupted video file")
        print("- Missing OpenCV dependencies")


def main():
    """Main function."""
    if len(sys.argv) != 2:
        print("Usage: python examples/simple_video_demo.py /path/to/video.mp4")
        print("\nExample:")
        print("  python examples/simple_video_demo.py ~/Downloads/sample_video.mp4")
        sys.exit(1)
    
    video_path = sys.argv[1]
    analyze_video_file(video_path)


if __name__ == "__main__":
    main()