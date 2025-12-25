#!/usr/bin/env python3
"""
Demo script for VideoProcessor functionality.

This script demonstrates the VideoProcessor capabilities with local MP4 files.
It can either use a provided video file or create a simple test video.
"""

import sys
import os
import tempfile
import cv2
import numpy as np
from pathlib import Path

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.analysis.video_processor import VideoProcessor
from src.models.content import VideoFile


def create_test_video(output_path: str, duration_seconds: int = 5, fps: int = 30) -> str:
    """
    Create a simple test video with text overlays and moving objects.
    
    Args:
        output_path: Path where to save the test video
        duration_seconds: Duration of the video in seconds
        fps: Frames per second
        
    Returns:
        Path to the created video file
    """
    print(f"Creating test video: {output_path}")
    
    # Video properties
    width, height = 640, 480
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    
    # Create video writer
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    total_frames = duration_seconds * fps
    
    for frame_num in range(total_frames):
        # Create a frame with gradient background
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Create gradient background
        for y in range(height):
            color_value = int(255 * y / height)
            frame[y, :] = [color_value // 3, color_value // 2, color_value]
        
        # Add moving circle
        circle_x = int(width * (frame_num / total_frames))
        circle_y = height // 2
        cv2.circle(frame, (circle_x, circle_y), 30, (0, 255, 255), -1)
        
        # Add text overlays that change over time
        texts = [
            "Instagram Content Analyzer Demo",
            "VideoProcessor Test",
            f"Frame {frame_num + 1}/{total_frames}",
            "OpenCV Generated Video"
        ]
        
        # Add different text at different times
        if frame_num < total_frames // 4:
            text = texts[0]
        elif frame_num < total_frames // 2:
            text = texts[1]
        elif frame_num < 3 * total_frames // 4:
            text = texts[2]
        else:
            text = texts[3]
        
        # Add text overlay
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.7
        color = (255, 255, 255)
        thickness = 2
        
        # Get text size for centering
        text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
        text_x = (width - text_size[0]) // 2
        text_y = 50
        
        # Add black background for text
        cv2.rectangle(frame, (text_x - 10, text_y - 30), 
                     (text_x + text_size[0] + 10, text_y + 10), (0, 0, 0), -1)
        
        # Add text
        cv2.putText(frame, text, (text_x, text_y), font, font_scale, color, thickness)
        
        # Add some objects for detection
        if frame_num % 30 < 15:  # Show for half the time
            # Add rectangle (simulating a product/object)
            cv2.rectangle(frame, (50, 100), (150, 200), (0, 255, 0), 3)
            cv2.putText(frame, "Product", (60, 130), font, 0.5, (255, 255, 255), 1)
        
        if frame_num % 45 < 20:  # Show at different intervals
            # Add another object
            cv2.rectangle(frame, (width - 150, height - 150), (width - 50, height - 50), (255, 0, 0), 3)
            cv2.putText(frame, "Brand Logo", (width - 140, height - 100), font, 0.4, (255, 255, 255), 1)
        
        # Write frame
        out.write(frame)
    
    # Release video writer
    out.release()
    
    print(f"Test video created successfully: {output_path}")
    return output_path


def demo_video_processor(video_path: str = None):
    """
    Demonstrate VideoProcessor functionality.
    
    Args:
        video_path: Path to video file to process (optional)
    """
    print("=== VideoProcessor Demo ===\n")
    
    # Initialize processor
    processor = VideoProcessor()
    
    # Determine video file to use
    if video_path and os.path.exists(video_path):
        print(f"Using provided video file: {video_path}")
        test_video_path = video_path
        cleanup_video = False
    else:
        print("No video file provided or file not found. Creating test video...")
        # Create test video in temp directory
        temp_dir = tempfile.mkdtemp()
        test_video_path = os.path.join(temp_dir, "test_video.mp4")
        create_test_video(test_video_path, duration_seconds=3, fps=10)  # Shorter for demo
        cleanup_video = True
    
    try:
        # Get video info
        cap = cv2.VideoCapture(test_video_path)
        if not cap.isOpened():
            print(f"Error: Could not open video file {test_video_path}")
            return
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = frame_count / fps if fps > 0 else 0
        
        cap.release()
        
        print(f"\nVideo Information:")
        print(f"  Path: {test_video_path}")
        print(f"  Duration: {duration:.2f} seconds")
        print(f"  FPS: {fps:.2f}")
        print(f"  Resolution: {width}x{height}")
        print(f"  Total Frames: {frame_count}")
        
        # Create VideoFile object
        video_file = VideoFile(
            file_path=test_video_path,
            duration=duration,
            fps=int(fps),
            resolution=(width, height)
        )
        
        print(f"\n1. Frame Extraction:")
        print("   Extracting frames from video...")
        
        # Extract frames
        frames = processor.extract_frames(video_file, max_frames=5)
        print(f"   Extracted {len(frames)} frames")
        
        for i, frame in enumerate(frames):
            print(f"   Frame {i+1}: {frame.timestamp:.2f}s, {frame.resolution[0]}x{frame.resolution[1]}")
        
        print(f"\n2. Frame Analysis (Mock - No OpenAI API):")
        print("   Note: This demo shows the structure without actual GPT-4V calls")
        print("   In production, each frame would be analyzed for:")
        print("   - Objects and items visible")
        print("   - Text overlays and readable text")
        print("   - Scene descriptions")
        print("   - People and activities")
        print("   - Brands and commercial elements")
        
        # Simulate frame analysis without API calls
        print(f"\n3. Simulated Analysis Results:")
        mock_objects = ["circle", "text overlay", "gradient background", "geometric shapes"]
        mock_text_overlays = ["Instagram Content Analyzer Demo", "VideoProcessor Test", "Frame counter"]
        
        print(f"   Detected Objects: {mock_objects}")
        print(f"   Text Overlays Found: {mock_text_overlays}")
        print(f"   Scene Description: Video with moving elements and text overlays")
        print(f"   Confidence Score: 0.85 (simulated)")
        
        print(f"\n4. Complete Video Processing:")
        print("   The process_video() method would:")
        print("   - Extract frames at optimal intervals")
        print("   - Analyze each frame with GPT-4V")
        print("   - Aggregate results across all frames")
        print("   - Remove duplicate detections")
        print("   - Calculate overall confidence scores")
        print("   - Clean up temporary frame files")
        
        # Clean up frame files
        print(f"\n5. Cleanup:")
        processor.cleanup_temp_files(frames)
        print("   Temporary frame files cleaned up")
        
        print(f"\n=== VideoProcessor Demo Complete ===")
        
        if not cleanup_video:
            print(f"\nYour video file was processed successfully!")
            print(f"To test with OpenAI integration, set up your API key in .env file")
        
    except Exception as e:
        print(f"Error during video processing: {str(e)}")
        
    finally:
        # Clean up test video if we created it
        if cleanup_video and os.path.exists(test_video_path):
            try:
                os.unlink(test_video_path)
                os.rmdir(os.path.dirname(test_video_path))
                print("Test video cleaned up")
            except OSError:
                pass


def main():
    """Main function to run the demo."""
    import argparse
    
    parser = argparse.ArgumentParser(description="VideoProcessor Demo")
    parser.add_argument("--video", "-v", type=str, help="Path to MP4 video file to process")
    parser.add_argument("--create-test", "-t", action="store_true", 
                       help="Create a test video file and save it")
    
    args = parser.parse_args()
    
    if args.create_test:
        # Create and save a test video
        output_path = "test_video_demo.mp4"
        create_test_video(output_path, duration_seconds=10, fps=30)
        print(f"\nTest video created: {output_path}")
        print("You can now run the demo with: python examples/video_processor_demo.py --video test_video_demo.mp4")
        return
    
    # Run the demo
    demo_video_processor(args.video)


if __name__ == "__main__":
    main()