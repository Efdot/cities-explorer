#!/usr/bin/env python3
"""
Generate a loading city animation with rough edges and 8fps choppy style.
Creates an abstract city that builds up with a hand-drawn, sketchy aesthetic.
"""

from PIL import Image, ImageDraw
import random
import math

# Configuration
WIDTH, HEIGHT = 200, 200
FRAMES = 24  # 24 frames at 8fps = 3 seconds
FPS = 8  # Choppy animation style
FRAME_DURATION = int(1000 / FPS)  # ms per frame

# Warm color palette (simplified to 5 colors as requested)
COLORS = [
    (232, 120, 50),   # Deep orange
    (244, 165, 80),   # Mid orange
    (255, 200, 100),  # Warm yellow
    (50, 45, 55),     # Dark charcoal
    (255, 252, 245),  # Warm white
]

# Color weights for city elements
BUILDING_COLORS = COLORS[:3]  # Oranges and yellow
DETAIL_COLORS = [COLORS[3], COLORS[4]]  # Charcoal and white

def add_rough_edge(draw, x1, y1, x2, y2, color, width=2):
    """Draw a line with rough, hand-drawn feel"""
    steps = max(3, int(math.sqrt((x2-x1)**2 + (y2-y1)**2) / 8))
    points = []
    for i in range(steps + 1):
        t = i / steps
        px = x1 + (x2 - x1) * t
        py = y1 + (y2 - y1) * t
        # Add jitter for rough edges
        jitter = random.uniform(-2, 2)
        px += jitter
        py += jitter * 0.5
        points.append((px, py))

    for i in range(len(points) - 1):
        draw.line([points[i], points[i+1]], fill=color, width=width)

def draw_rough_rect(draw, x, y, w, h, fill_color, outline_color=None):
    """Draw a rectangle with rough, imperfect edges"""
    # Fill with solid color
    draw.rectangle([x, y, x+w, y+h], fill=fill_color)

    # Add rough outline
    if outline_color:
        add_rough_edge(draw, x, y, x+w, y, outline_color)
        add_rough_edge(draw, x+w, y, x+w, y+h, outline_color)
        add_rough_edge(draw, x+w, y+h, x, y+h, outline_color)
        add_rough_edge(draw, x, y+h, x, y, outline_color)

def generate_buildings(seed):
    """Generate building data for consistent animation"""
    random.seed(seed)
    buildings = []

    # Create various buildings
    x = 10
    while x < WIDTH - 20:
        w = random.randint(15, 40)
        h = random.randint(40, 140)
        color = random.choice(BUILDING_COLORS)
        buildings.append({
            'x': x,
            'w': w,
            'h': h,
            'color': color,
            'windows': random.randint(2, 6),
            'style': random.choice(['box', 'pointed', 'rounded'])
        })
        x += w + random.randint(3, 12)

    return buildings

def draw_frame(frame_num, buildings, total_frames):
    """Draw a single frame with progressive building reveal"""
    img = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    progress = frame_num / (total_frames - 1)

    # Ground line with rough edge
    ground_y = HEIGHT - 20
    add_rough_edge(draw, 0, ground_y, WIDTH, ground_y + random.uniform(-1, 1), COLORS[3], width=2)

    # Draw buildings progressively
    num_buildings = int(len(buildings) * min(1.0, progress * 1.3))

    for i, b in enumerate(buildings[:num_buildings]):
        # Building height animation
        building_progress = min(1.0, (progress * len(buildings) - i) / 2)
        if building_progress <= 0:
            continue

        current_h = int(b['h'] * building_progress)
        y = ground_y - current_h

        # Add some frame-to-frame jitter for sketchy feel
        jitter_x = random.uniform(-1, 1)
        jitter_y = random.uniform(-1, 1)

        # Main building body
        draw_rough_rect(draw,
                       b['x'] + jitter_x, y + jitter_y,
                       b['w'], current_h,
                       b['color'], COLORS[3])

        # Windows (only if building is mostly drawn)
        if building_progress > 0.5:
            window_rows = min(b['windows'], int(current_h / 18))
            for row in range(window_rows):
                wy = y + 10 + row * 16
                for col in range(2):
                    wx = b['x'] + 5 + col * int((b['w'] - 10) / 2) + random.uniform(-1, 1)
                    window_color = random.choice(DETAIL_COLORS)
                    draw.rectangle([wx, wy, wx + 6, wy + 8], fill=window_color)

        # Rooftop details for some buildings
        if building_progress > 0.9 and b['style'] == 'pointed':
            peak_x = b['x'] + b['w'] / 2
            add_rough_edge(draw, b['x'], y, peak_x, y - 12, b['color'])
            add_rough_edge(draw, peak_x, y - 12, b['x'] + b['w'], y, b['color'])

    # Add some atmospheric elements in later frames
    if progress > 0.5:
        # Random dots/texture
        for _ in range(int(10 * progress)):
            px = random.randint(0, WIDTH)
            py = random.randint(0, ground_y - 20)
            if random.random() > 0.7:
                draw.point((px, py), fill=COLORS[4] + (100,))

    return img

def main():
    print("Generating rough city animation at 8fps...")

    # Generate consistent building layout
    buildings = generate_buildings(42)  # Fixed seed for reproducibility

    frames = []
    for i in range(FRAMES):
        print(f"  Frame {i+1}/{FRAMES}")
        frame = draw_frame(i, buildings, FRAMES)
        frames.append(frame)

    # Save as animated GIF with 8fps (125ms per frame)
    output_path = '/Users/efdotstudio/Downloads/cities-test-environment/loading-city.gif'
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=FRAME_DURATION,
        loop=0,
        disposal=2,
        transparency=0
    )

    print(f"Saved to {output_path}")
    print(f"  - {FRAMES} frames at {FPS}fps = {FRAMES/FPS:.1f} seconds")
    print(f"  - Frame duration: {FRAME_DURATION}ms")

if __name__ == '__main__':
    main()
