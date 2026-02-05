#!/usr/bin/env python3
"""
Generate animation with:
- Muted, less bright colors
- Lines at ~34-35 degree angles
- Golden ratio based opacity field
- Domino/light-filling-room fade in effect
- 8fps choppy vibe
- Mono weight: all strokes and dots same thickness (4px)
- Centered blob glyph animation with clear zone around it
"""

from PIL import Image, ImageDraw, ImageFilter
import math
import random

# Configuration - optimized for faster loading
WIDTH, HEIGHT = 160, 160  # Slightly smaller, scales in browser
FRAMES = 30  # 30 frames: fade in + hold + FAT fade out with color reveal at end
FPS = 8
FRAME_DURATION = int(1000 / FPS)

# Mono weight - all strokes and dots use this diameter (thinner base)
STROKE_WIDTH = 3
DOT_RADIUS = 1.5  # Slightly thinner dots

# Golden ratio for opacity calculations
PHI = 1.618033988749

# Pure grayscale palette - starts dark, ends light/white
COLORS = [
    (40, 40, 40),      # 1. Near black
    (55, 55, 55),      # 2. Very dark
    (70, 70, 70),      # 3. Dark gray
    (85, 85, 85),      # 4. Medium dark
    (100, 100, 100),   # 5. Medium gray
    (115, 115, 115),   # 6. Medium light
    (130, 130, 130),   # 7. Light gray
    (150, 150, 150),   # 8. Lighter
    (170, 170, 170),   # 9. Very light
    (190, 190, 190),   # 10. Near white
]

# Blob configuration - rule of thirds positioning (random quadrant each load)
# Four possible positions: top-left, top-right, bottom-left, bottom-right
BLOB_POSITIONS = [
    (int(WIDTH / 3), int(HEIGHT / 3)),         # Top-left third
    (int(WIDTH * 2 / 3), int(HEIGHT / 3)),     # Top-right third
    (int(WIDTH / 3), int(HEIGHT * 2 / 3)),     # Bottom-left third
    (int(WIDTH * 2 / 3), int(HEIGHT * 2 / 3)), # Bottom-right third
]
# Will be set randomly in main()
BLOB_CENTER_X = int(WIDTH / 3)
BLOB_CENTER_Y = int(HEIGHT * 2 / 3)
BLOB_SIZE = 80  # Proportionally scaled blob
CLEAR_ZONE_RADIUS = 22  # Proportionally scaled clear zone

# Keep CENTER_X/Y for shape calculations (center of canvas)
CENTER_X, CENTER_Y = WIDTH // 2, HEIGHT // 2

# Path to blob animation
BLOB_GIF_PATH = '/Users/efdotstudio/Downloads/cities-test-environment/loading-blob-light.gif'

def load_blob_frames():
    """Load all frames from the blob GIF animation"""
    try:
        blob_gif = Image.open(BLOB_GIF_PATH)
        frames = []

        try:
            while True:
                # Convert frame to RGBA
                frame = blob_gif.convert('RGBA')

                # Resize to target size
                frame = frame.resize((BLOB_SIZE, BLOB_SIZE), Image.Resampling.LANCZOS)

                frames.append(frame)
                blob_gif.seek(blob_gif.tell() + 1)
        except EOFError:
            pass

        print(f"  Loaded {len(frames)} blob frames at {BLOB_SIZE}x{BLOB_SIZE}px")
        return frames
    except Exception as e:
        print(f"  Could not load blob GIF: {e}")
        return None

def apply_color_reveal_to_frame(frame, color_progress):
    """Apply grayscale-to-color reveal effect to a frame"""
    if color_progress >= 1.0:
        return frame

    result = frame.copy()
    pixels = result.load()
    width, height = result.size

    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]

            if a > 0:
                # Calculate grayscale
                gray = int(0.299 * r + 0.587 * g + 0.114 * b)

                # Blend from gray to color
                r = int(gray + (r - gray) * color_progress)
                g = int(gray + (g - gray) * color_progress)
                b = int(gray + (b - gray) * color_progress)

                pixels[x, y] = (r, g, b, a)

    return result

def is_in_clear_zone(x, y):
    """Check if a point is in the clear zone around the blob (rule of thirds position)"""
    dx = x - BLOB_CENTER_X
    dy = y - BLOB_CENTER_Y
    dist = math.sqrt(dx*dx + dy*dy)
    return dist < CLEAR_ZONE_RADIUS

def line_intersects_clear_zone(x1, y1, x2, y2):
    """Check if a line segment passes through or near the clear zone"""
    # Check if either endpoint is in clear zone
    if is_in_clear_zone(x1, y1) or is_in_clear_zone(x2, y2):
        return True

    # Check if line passes through clear zone
    # Find closest point on line to blob center (dynamic position)
    dx = x2 - x1
    dy = y2 - y1
    line_len_sq = dx*dx + dy*dy

    if line_len_sq == 0:
        return is_in_clear_zone(x1, y1)

    t = max(0, min(1, ((BLOB_CENTER_X - x1) * dx + (BLOB_CENTER_Y - y1) * dy) / line_len_sq))
    closest_x = x1 + t * dx
    closest_y = y1 + t * dy

    return is_in_clear_zone(closest_x, closest_y)

def golden_opacity(x, y, base_alpha=120):
    """Calculate opacity based on golden ratio spiral from center"""
    cx, cy = WIDTH / 2, HEIGHT / 2
    dx, dy = x - cx, y - cy
    dist = math.sqrt(dx*dx + dy*dy)
    angle = math.atan2(dy, dx)
    spiral_factor = (dist / 100) * PHI
    angle_factor = (angle + math.pi) / (2 * math.pi)
    golden_mod = math.sin(spiral_factor * PHI + angle_factor * math.pi * 2) * 0.3
    opacity = base_alpha * (0.7 + golden_mod)
    return max(40, min(160, int(opacity)))

def with_alpha(color, alpha):
    """Add alpha to RGB color"""
    return (color[0], color[1], color[2], alpha)

def grayscale_to_color(color, color_progress):
    """Blend from grayscale to full color based on progress (0=gray, 1=color)"""
    gray = int(0.299 * color[0] + 0.587 * color[1] + 0.114 * color[2])
    r = int(gray + (color[0] - gray) * color_progress)
    g = int(gray + (color[1] - gray) * color_progress)
    b = int(gray + (color[2] - gray) * color_progress)
    return (r, g, b)

def draw_dot(draw, x, y, r, color):
    """Single dot with very subtle roughness"""
    jitter = random.uniform(-0.15, 0.15)
    draw.ellipse([x-r+jitter, y-r+jitter, x+r+jitter, y+r+jitter], fill=color)

def draw_dotted_line(draw, x1, y1, x2, y2, color, stroke_w, dot_r, dot_spacing=8):
    """Line made of dots with very subtle roughness - mono weight"""
    dist = math.sqrt((x2-x1)**2 + (y2-y1)**2)
    if dist < 1:
        return
    num_dots = max(2, int(dist / dot_spacing))
    for i in range(num_dots):
        t = i / (num_dots - 1) if num_dots > 1 else 0
        px = x1 + (x2 - x1) * t + random.uniform(-0.2, 0.2)
        py = y1 + (y2 - y1) * t + random.uniform(-0.2, 0.2)
        draw_dot(draw, px, py, dot_r, color)

def draw_mini_curve(draw, cx, cy, radius, color, stroke_w, dot_r):
    """Small curved segment - like a tiny arc - mono weight with subtle noise"""
    start_deg = random.uniform(0, 360)
    sweep = random.uniform(40, 80)
    points = []
    steps = 8  # More steps for smoother curve
    for i in range(steps + 1):
        t = i / steps
        angle = math.radians(start_deg + t * sweep)
        jitter = random.uniform(-0.1, 0.1)  # Very subtle jitter
        px = cx + math.cos(angle) * radius + jitter
        py = cy + math.sin(angle) * radius + jitter
        points.append((px, py))

    r = dot_r
    for i in range(len(points) - 1):
        draw.line([points[i], points[i+1]], fill=color, width=int(stroke_w))
    # Rounded end caps
    draw.ellipse([points[0][0]-r, points[0][1]-r, points[0][0]+r, points[0][1]+r], fill=color)
    draw.ellipse([points[-1][0]-r, points[-1][1]-r, points[-1][0]+r, points[-1][1]+r], fill=color)

def draw_dashed_line(draw, x1, y1, x2, y2, color, stroke_w, dot_r, dash_len=6, gap_len=6):
    """Line made of SHORT dashes with very subtle roughness and rounded caps - mono weight"""
    dist = math.sqrt((x2-x1)**2 + (y2-y1)**2)
    if dist < 1:
        return
    dx = (x2 - x1) / dist
    dy = (y2 - y1) / dist

    r = dot_r
    pos = 0
    while pos < dist:
        jx, jy = random.uniform(-0.15, 0.15), random.uniform(-0.15, 0.15)
        sx = x1 + dx * pos + jx
        sy = y1 + dy * pos + jy
        end_pos = min(pos + dash_len, dist)
        ex = x1 + dx * end_pos + random.uniform(-0.15, 0.15)
        ey = y1 + dy * end_pos + random.uniform(-0.15, 0.15)

        draw.line([(sx, sy), (ex, ey)], fill=color, width=int(stroke_w))
        draw.ellipse([sx-r, sy-r, sx+r, sy+r], fill=color)
        draw.ellipse([ex-r, ey-r, ex+r, ey+r], fill=color)

        pos += dash_len + gap_len

def draw_solid_line(draw, x1, y1, x2, y2, color, stroke_w, dot_r):
    """Solid line with rounded caps and very subtle roughness - mono weight"""
    jx1, jy1 = random.uniform(-0.1, 0.1), random.uniform(-0.1, 0.1)
    jx2, jy2 = random.uniform(-0.1, 0.1), random.uniform(-0.1, 0.1)
    draw.line([(x1+jx1, y1+jy1), (x2+jx2, y2+jy2)], fill=color, width=int(stroke_w))
    r = dot_r
    draw.ellipse([x1-r+jx1, y1-r+jy1, x1+r+jx1, y1+r+jy1], fill=color)
    draw.ellipse([x2-r+jx2, y2-r+jy2, x2+r+jx2, y2+r+jy2], fill=color)

def draw_arch(draw, cx, cy, radius, start_deg, end_deg, color, stroke_w, dot_r, dotted=False, dashed=False):
    """Arc/arch with optional dotted or dashed style - mono weight with subtle noise"""
    points = []
    steps = 20  # More steps for smoother arcs
    for i in range(steps + 1):
        t = i / steps
        angle = math.radians(start_deg + t * (end_deg - start_deg))
        jitter = random.uniform(-0.12, 0.12)  # Very subtle jitter
        px = cx + math.cos(angle) * radius + jitter
        py = cy + math.sin(angle) * radius + jitter
        points.append((px, py))

    r = dot_r

    if dotted:
        for px, py in points[::2]:
            if not is_in_clear_zone(px, py):
                draw_dot(draw, px, py, dot_r, color)
    elif dashed:
        for i in range(0, len(points) - 1, 3):
            if i + 1 < len(points):
                if not is_in_clear_zone(points[i][0], points[i][1]) and not is_in_clear_zone(points[i+1][0], points[i+1][1]):
                    draw.line([points[i], points[i+1]], fill=color, width=int(stroke_w))
                    draw.ellipse([points[i][0]-r, points[i][1]-r, points[i][0]+r, points[i][1]+r], fill=color)
                    draw.ellipse([points[i+1][0]-r, points[i+1][1]-r, points[i+1][0]+r, points[i+1][1]+r], fill=color)
    else:
        for i in range(len(points) - 1):
            if not is_in_clear_zone(points[i][0], points[i][1]) and not is_in_clear_zone(points[i+1][0], points[i+1][1]):
                draw.line([points[i], points[i+1]], fill=color, width=int(stroke_w))
        if not is_in_clear_zone(points[0][0], points[0][1]):
            draw.ellipse([points[0][0]-r, points[0][1]-r, points[0][0]+r, points[0][1]+r], fill=color)
        if not is_in_clear_zone(points[-1][0], points[-1][1]):
            draw.ellipse([points[-1][0]-r, points[-1][1]-r, points[-1][0]+r, points[-1][1]+r], fill=color)

def line_at_angle(x, y, length, angle_deg):
    """Calculate line endpoints at given angle"""
    angle_rad = math.radians(angle_deg)
    x2 = x + math.cos(angle_rad) * length
    y2 = y + math.sin(angle_rad) * length
    return (x, y, x2, y2)

def get_balanced_color_idx(x, y, shape_id):
    """
    Picasso-like color distribution - balanced mix throughout.
    Uses position as a subtle influence but distributes all 10 colors everywhere.
    """
    # Calculate distance from center (normalized 0-1)
    dx = (x - CENTER_X) / (WIDTH / 2)
    dy = (y - CENTER_Y) / (HEIGHT / 2)
    dist_from_center = math.sqrt(dx*dx + dy*dy)
    dist_from_center = min(1.0, dist_from_center)

    # Use shape_id for base distribution to ensure variety
    base_idx = shape_id % len(COLORS)

    # Add some randomness with slight position influence
    # 60% chance: use distributed base color
    # 25% chance: random from all colors
    # 15% chance: position-influenced pick

    roll = random.random()

    if roll < 0.60:
        # Distributed cycling through all colors
        return base_idx
    elif roll < 0.85:
        # Pure random from all 10 colors
        return random.randint(0, len(COLORS) - 1)
    else:
        # Slight position influence - but still mixed
        if dist_from_center < 0.5:
            # Center area - slight preference for lighter but include some dark
            weights = [2, 2, 1.5, 1, 1, 2, 1.5, 1, 0.8, 0.6]  # greys + light sepias
        else:
            # Edge area - slight preference for darker but include some light
            weights = [1, 1.2, 1.5, 2, 2, 1, 1.5, 2, 2, 1.8]  # darker greys + sepias

        # Weighted random choice
        total = sum(weights)
        r = random.uniform(0, total)
        cumulative = 0
        for i, w in enumerate(weights):
            cumulative += w
            if r <= cumulative:
                return i
        return len(COLORS) - 1

def get_shapes():
    """City blocks with variety - bricks, dashes, dots, and arcs"""
    shapes = []

    # Main angles for brick/city feel
    MAIN_ANGLE = 35
    ANGLES = [MAIN_ANGLE, -MAIN_ANGLE, MAIN_ANGLE + 90, -MAIN_ANGLE - 90]

    shape_data = []

    # Grid for structured placement
    grid_size = 6
    cell_w = WIDTH / grid_size
    cell_h = HEIGHT / grid_size

    shape_id = 0
    for row in range(grid_size):
        for col in range(grid_size):
            # Staggered brick pattern - offset every other row
            offset_x = (cell_w * 0.3) if row % 2 == 1 else 0
            bx = col * cell_w + cell_w / 2 + offset_x + random.uniform(-6, 6)
            by = row * cell_h + cell_h / 2 + random.uniform(-6, 6)

            # Wrap around for offset rows
            if bx > WIDTH - 10:
                bx -= WIDTH - 20

            # Skip clear zone around blob
            if is_in_clear_zone(bx, by):
                shape_id += 1
                continue

            # Domino timing based on diagonal distance from top-left
            domino_delay = (row + col) / (grid_size * 2 - 2)

            # Mix of angles - mostly alternating by row, some random
            if random.random() > 0.2:
                angle = ANGLES[row % 2]  # Alternating brick courses
            else:
                angle = random.choice(ANGLES)  # Occasional variety

            # Varied line lengths
            length = random.uniform(14, 36)

            # Mix of line types - solid, dashed, dotted
            roll = random.random()
            if roll < 0.45:
                shape_type = 'solid'
            elif roll < 0.75:
                shape_type = 'dashed'
            else:
                shape_type = 'dotted'

            # Sequential grayscale distribution
            color_idx = (shape_id * 2) % len(COLORS)

            # Get line coordinates
            x1, y1, x2, y2 = line_at_angle(bx, by, length, angle)

            # Keep in bounds
            x1, x2 = max(5, min(155, x1)), max(5, min(155, x2))
            y1, y2 = max(5, min(155, y1)), max(5, min(155, y2))

            shape_data.append({
                'type': shape_type,
                'coords': (x1, y1, x2, y2),
                'color_idx': color_idx,
                'domino': domino_delay,
                'cx': (x1 + x2) / 2,
                'cy': (y1 + y2) / 2
            })

            shape_id += 1

    # Scattered dots
    for i in range(8):
        gx = random.uniform(15, WIDTH - 15)
        gy = random.uniform(15, HEIGHT - 15)

        if is_in_clear_zone(gx, gy):
            continue

        domino = (gx / WIDTH + gy / HEIGHT) / 2

        shape_data.append({
            'type': 'dot',
            'coords': (gx, gy, DOT_RADIUS),
            'color_idx': (i * 2) % len(COLORS),
            'domino': domino,
            'cx': gx,
            'cy': gy
        })

    # Add some arcs/arches for variety
    for i in range(5):
        ax = random.uniform(25, WIDTH - 25)
        ay = random.uniform(25, HEIGHT - 25)

        if is_in_clear_zone(ax, ay):
            continue

        radius = random.uniform(10, 20)
        start = random.choice(ANGLES)
        sweep = random.uniform(50, 100)

        domino = (ax / WIDTH + ay / HEIGHT) / 2

        # Mix of arch styles
        arch_style = random.random()
        shape_data.append({
            'type': 'arch',
            'coords': (ax, ay, radius, start, start + sweep),
            'color_idx': (i * 3) % len(COLORS),
            'domino': domino,
            'cx': ax,
            'cy': ay,
            'dotted': arch_style < 0.3,
            'dashed': 0.3 <= arch_style < 0.6
        })

    return shape_data

def ease_out_cubic(t):
    """Easing function for smooth light-filling effect"""
    return 1 - pow(1 - t, 3)

def ease_in_quad(t):
    """Slow start easing - like a dimmer switch turning on"""
    return t * t

def draw_shape_to_layer(draw, shape, color, current_stroke_w, current_dot_r, eased_progress, stroke_mult):
    """Draw a single shape to a layer"""
    if shape['type'] == 'dot':
        x, y, r = shape['coords']
        r_anim = r * eased_progress * stroke_mult
        if r_anim > 0.5 and not is_in_clear_zone(x, y):
            draw_dot(draw, x, y, r_anim, color)

    elif shape['type'] in ['dotted', 'dashed', 'solid', 'mini_curve']:
        x1, y1, x2, y2 = shape['coords']
        draw_progress = min(1.0, eased_progress * 1.2)
        px = x1 + (x2 - x1) * draw_progress
        py = y1 + (y2 - y1) * draw_progress

        if shape['type'] == 'dotted':
            draw_dotted_line(draw, x1, y1, px, py, color, current_stroke_w, current_dot_r)
        elif shape['type'] == 'dashed':
            draw_dashed_line(draw, x1, y1, px, py, color, current_stroke_w, current_dot_r)
        elif shape['type'] == 'solid':
            draw_solid_line(draw, x1, y1, px, py, color, current_stroke_w, current_dot_r)
        elif shape['type'] == 'mini_curve':
            mid_x = (x1 + px) / 2
            mid_y = (y1 + py) / 2
            if not is_in_clear_zone(mid_x, mid_y):
                radius = random.uniform(8, 16)
                draw_mini_curve(draw, mid_x, mid_y, radius, color, current_stroke_w, current_dot_r)

    elif shape['type'] == 'arch':
        cx, cy, radius, start, end = shape['coords']
        draw_progress = min(1.0, eased_progress * 1.2)
        current_end = start + (end - start) * draw_progress
        dotted = shape.get('dotted', False)
        dashed = shape.get('dashed', False)
        draw_arch(draw, cx, cy, radius, start, current_end, color, current_stroke_w, current_dot_r, dotted, dashed)


def draw_frame(frame_num, shapes, blob_frames):
    """Draw a single frame - fade in → hold → FAT bokeh fade out in layers"""
    # Overall animation progress (0 to 1)
    total_progress = frame_num / (FRAMES - 1)

    # Animation phases - ALL GRAYSCALE
    # 0-50%: Fade in from darkness (domino cascade)
    # 50-65%: Hold at full
    # 65-100%: FAT bokeh fade out in cascading layers

    if total_progress < 0.50:
        # Fade in phase
        fade_in_progress = total_progress / 0.50
        dimmer = ease_in_quad(fade_in_progress)
        fade_out = 1.0
        stroke_mult = 1.0
        blur_phase = 0.0
    elif total_progress < 0.65:
        # Hold phase
        dimmer = 1.0
        fade_out = 1.0
        stroke_mult = 1.0
        blur_phase = 0.0
    else:
        # FAT bokeh fade out phase - complete by 95% so last frames are clean
        fade_out_progress = (total_progress - 0.65) / 0.30  # Faster fade (30% not 35%)
        fade_out_progress = min(1.0, fade_out_progress)
        dimmer = 1.0
        # Opacity fades more aggressively - cubic for faster end
        fade_out = max(0, 1.0 - (fade_out_progress * fade_out_progress * fade_out_progress))
        stroke_mult = 1.0 + fade_out_progress * 3.0  # Lines get 1x to 4x FAT
        blur_phase = fade_out_progress

    # Current stroke sizes (affected by FAT multiplier)
    current_stroke_w = STROKE_WIDTH * stroke_mult
    current_dot_r = DOT_RADIUS * stroke_mult

    random.seed(frame_num * 42)

    # During blur phase, render in layers for cascading bokeh effect
    NUM_LAYERS = 3
    if blur_phase > 0:
        layers = []
        for layer_idx in range(NUM_LAYERS):
            layer_img = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
            layer_draw = ImageDraw.Draw(layer_img, 'RGBA')

            for shape in shapes:
                shape_start = shape['domino'] * 0.5

                if total_progress < shape_start:
                    continue

                # Assign shapes to layers based on domino timing
                shape_layer = int(shape['domino'] * NUM_LAYERS)
                if shape_layer != layer_idx:
                    continue

                local_progress = (total_progress - shape_start) / (1 - shape_start)
                local_progress = min(1.0, local_progress * 1.5)
                eased_progress = ease_out_cubic(local_progress)

                if eased_progress < 0.05:
                    continue

                base_opacity = golden_opacity(shape['cx'], shape['cy'], base_alpha=110)
                current_opacity = int(base_opacity * eased_progress * dimmer * fade_out)

                base_color = COLORS[shape['color_idx']]
                color = with_alpha(base_color, current_opacity)

                draw_shape_to_layer(layer_draw, shape, color, current_stroke_w, current_dot_r, eased_progress, stroke_mult)

            layers.append(layer_img)

        # Composite layers with cascading blur - earlier layers blur first/more
        img = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
        for layer_idx, layer_img in enumerate(layers):
            # Earlier layers (appeared first) blur sooner and more
            layer_blur_offset = layer_idx / NUM_LAYERS * 0.3
            layer_blur_progress = max(0, (blur_phase - layer_blur_offset) / (1 - layer_blur_offset))
            blur_radius = layer_blur_progress * 5  # Max 5px blur

            if blur_radius > 0.5:
                layer_img = layer_img.filter(ImageFilter.GaussianBlur(radius=blur_radius))

            img = Image.alpha_composite(img, layer_img)
    else:
        # Normal rendering (no blur)
        img = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img, 'RGBA')

        for shape in shapes:
            shape_start = shape['domino'] * 0.5

            if total_progress < shape_start:
                continue

            local_progress = (total_progress - shape_start) / (1 - shape_start)
            local_progress = min(1.0, local_progress * 1.5)
            eased_progress = ease_out_cubic(local_progress)

            if eased_progress < 0.05:
                continue

            base_opacity = golden_opacity(shape['cx'], shape['cy'], base_alpha=110)
            current_opacity = int(base_opacity * eased_progress * dimmer * fade_out)

            base_color = COLORS[shape['color_idx']]
            color = with_alpha(base_color, current_opacity)

            draw_shape_to_layer(draw, shape, color, current_stroke_w, current_dot_r, eased_progress, stroke_mult)

    # Composite the blob glyph animation
    if blob_frames:
        blob_frame_idx = frame_num % len(blob_frames)
        blob_frame = blob_frames[blob_frame_idx].copy()

        blob_frame = apply_color_reveal_to_frame(blob_frame, 0.0)

        blob_start = 0.15
        if total_progress > blob_start:
            blob_opacity = min(1.0, (total_progress - blob_start) / 0.4) * dimmer * fade_out

            # Apply blur to blob during fade out (starts later than shapes)
            if blur_phase > 0.3:
                blob_blur = (blur_phase - 0.3) * 4
                blob_frame = blob_frame.filter(ImageFilter.GaussianBlur(radius=blob_blur))

            if blob_opacity < 1.0:
                blob_alpha = blob_frame.split()[3]
                blob_alpha = blob_alpha.point(lambda x: int(x * blob_opacity))
                blob_frame.putalpha(blob_alpha)

            blob_x = BLOB_CENTER_X - BLOB_SIZE // 2
            blob_y = BLOB_CENTER_Y - BLOB_SIZE // 2

            img.paste(blob_frame, (blob_x, blob_y), blob_frame)

    return img

def main():
    global BLOB_CENTER_X, BLOB_CENTER_Y
    import time
    import os
    # Fresh composition each time using timestamp + random bytes for more entropy
    time_component = int(time.time() * 1000000) % 1000000
    random_component = int.from_bytes(os.urandom(4), 'big') % 1000000
    composition_seed = (time_component + random_component) % 1000000

    # Randomly pick a blob position from the four rule-of-thirds spots
    random.seed(composition_seed)
    blob_pos = random.choice(BLOB_POSITIONS)
    BLOB_CENTER_X, BLOB_CENTER_Y = blob_pos

    print(f"Generating fresh composition (seed: {composition_seed})...")
    print(f"  Mono weight: {STROKE_WIDTH}px strokes, {DOT_RADIUS*2}px dots")
    print(f"  Blob position: ({BLOB_CENTER_X}, {BLOB_CENTER_Y}) with {CLEAR_ZONE_RADIUS}px clear zone")
    print(f"  Animation: fade in → hold → FAT fade out")

    # Load blob animation frames
    blob_frames = load_blob_frames()

    # Keep the same seed for shapes so composition is consistent
    shapes = get_shapes()

    # Generate all frames (fade in + hold + FAT fade out)
    all_frames = []
    for i in range(FRAMES):
        print(f"  Frame {i+1}/{FRAMES}")
        frame = draw_frame(i, shapes, blob_frames)
        all_frames.append(frame)

    # Add a few fully transparent frames at the end to ensure clean exit
    transparent_frame = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
    for _ in range(3):
        all_frames.append(transparent_frame.copy())

    print(f"  Total frames: {len(all_frames)} ({len(all_frames)/FPS:.1f}s)")

    output_path = '/Users/efdotstudio/Downloads/cities-test-environment/loading-goo.gif'

    # Convert frames to strict grayscale RGBA, then save directly
    # The key is to ensure pixel values are truly R=G=B before any palette conversion
    grayscale_frames = []
    for frame in all_frames:
        # Get the alpha channel
        alpha = frame.split()[3]

        # Convert to true grayscale (L mode)
        gray = frame.convert('L')

        # Create new RGBA where R=G=B=gray value
        w, h = frame.size
        result = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        gray_pixels = gray.load()
        alpha_pixels = alpha.load()
        result_pixels = result.load()

        for y in range(h):
            for x in range(w):
                g = gray_pixels[x, y]
                a = alpha_pixels[x, y]
                result_pixels[x, y] = (g, g, g, a)

        grayscale_frames.append(result)

    # Save without aggressive quantization - let PIL handle it naturally
    grayscale_frames[0].save(
        output_path,
        save_all=True,
        append_images=grayscale_frames[1:],
        duration=FRAME_DURATION,
        loop=0,
        disposal=2,
        transparency=0
    )

    print(f"Saved to {output_path}")
    print(f"  - {FRAMES} frames at {FPS}fps = {FRAMES/FPS:.1f} seconds")

if __name__ == '__main__':
    main()
