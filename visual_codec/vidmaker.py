"""Videomaker module"""

import cv2
import numpy as np


def cvector_to_video(
    color_vector: bytes,
    output_path: str,
    frame_width: int,
    frame_height: int,
    fps: int = 1,
) -> int:
    """Generate video out of color vector"""

    frame_size = frame_width * frame_height

    n_pad = frame_size - (len(color_vector) % frame_size)

    color_vector += b"\x00" * n_pad

    frames = [
        color_vector[i : i + frame_size]
        for i in range(0, len(color_vector), frame_size)
    ]

    # Define the output video file name and properties
    fourcc = cv2.VideoWriter_fourcc(*"MPNG")
    frame_size = (frame_width, frame_height)

    # Create the VideoWriter object
    video_writer = cv2.VideoWriter(
        output_path, fourcc, fps, (frame_width, frame_height), 0
    )

    # Write each frame to the video file
    for i, frame in enumerate(frames):
        # Convert the frame from byte array to numpy array
        frame_np = np.frombuffer(frame, dtype=np.uint8)
        frame_np = frame_np.reshape((frame_height, frame_width))

        # Write the frame image to the video file
        video_writer.write(frame_np)

    # Release the VideoWriter object
    video_writer.release()

    return n_pad


def video_to_cvector(input_file: str, video_pad: int) -> bytes:
    """Extract color vector out of video file"""
    vidObj = cv2.VideoCapture(input_file)

    data_bytes = b""
    success = True
    while success:
        success, image = vidObj.read()

        if success:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            image_bytes = image.tobytes()
            data_bytes += image_bytes

    return data_bytes[:-video_pad]
