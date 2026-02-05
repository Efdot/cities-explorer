#!/usr/bin/env python3
"""
Lighten the blob animation - make it pure grayscale and translucent.
"""

from PIL import Image, ImageEnhance
import os

input_path = '/Users/efdotstudio/Downloads/cities-test-environment/loading-blob-transparent.gif'
output_path = '/Users/efdotstudio/Downloads/cities-test-environment/loading-blob-light.gif'

# Open the GIF
img = Image.open(input_path)

frames = []
durations = []

try:
    while True:
        # Get frame duration
        duration = img.info.get('duration', 100)
        durations.append(duration)

        # Convert to RGBA
        frame = img.convert('RGBA')

        # Get pixel data
        pixels = frame.load()
        width, height = frame.size

        # Lighten and warm up the colors
        for y in range(height):
            for x in range(width):
                r, g, b, a = pixels[x, y]

                if a > 0:  # Only modify non-transparent pixels
                    # Convert to pure grayscale - no warm tones
                    gray = int(0.299 * r + 0.587 * g + 0.114 * b)

                    # Lighten the grayscale slightly
                    lighten_factor = 0.35
                    gray = int(gray + (200 - gray) * lighten_factor)  # Shift toward light gray
                    gray = max(0, min(255, gray))

                    r, g, b = gray, gray, gray  # Pure grayscale

                    # Make slightly more translucent
                    a = int(a * 0.85)

                    # Clamp values
                    r = max(0, min(255, r))
                    g = max(0, min(255, g))
                    b = max(0, min(255, b))
                    a = max(0, min(255, a))

                    pixels[x, y] = (r, g, b, a)

        frames.append(frame.copy())

        img.seek(img.tell() + 1)
except EOFError:
    pass

# Save the lightened GIF
if frames:
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=durations[0] if durations else 100,
        loop=0,
        disposal=1,  # Do not dispose - keeps previous frame, avoids flashing
    )
    print(f"Saved lightened blob to {output_path}")
    print(f"  - {len(frames)} frames")
else:
    print("No frames found!")
