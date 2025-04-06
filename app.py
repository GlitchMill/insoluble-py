import os
import sys
from PIL import Image, ImageDraw, ImageFont, ImageOps
from typing import Optional, Literal, TypedDict
import numpy as np
import argparse

class EditorState(TypedDict):
    text: str
    color: str
    show_credits: bool
    background: str
    title_font_size: int
    subtitle_font_size: int
    outline: int
    outline_color: str
    effect: Optional[Literal['glitch', 'distort', 'shadow']]
    small_subtitle: str
    subtitle: str
    theme: str
    blood_level: Optional[int]

def get_asset_path(path: str) -> str:
    """Get the correct path for assets, whether running as script or compiled binary"""
    if getattr(sys, 'frozen', False):
        # Running as compiled binary
        base_path = sys._MEIPASS
    else:
        # Running as script
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, path)

def generate_title_card(state: EditorState, output_path: str = "output.png"):
    # Set fixed dimensions for consistent sizing
    WIDTH = 1920
    HEIGHT = 1080
    
    # Load background image (lossless PNG)
    if state.get('theme') == 'blood':
        # Blood mode: Almost black background
        image = Image.new('RGBA', (WIDTH, HEIGHT), (2, 0, 3, 255))  # #020003
    elif state.get('theme') == 'evil':
        # Evil mode: Yellow background
        image = Image.new('RGBA', (WIDTH, HEIGHT), (254, 228, 91, 255))  # #fee45b
    else:
        bg_path = get_asset_path(os.path.join('assets', 'background', 'blue.jpg'))  # Prefer PNG background
        try:
            if bg_path.endswith('.png'):
                image = Image.open(bg_path).convert('RGBA')
            else:
                image = Image.open(bg_path).convert('RGB')
            # Ensure consistent image size
            image = image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
        except FileNotFoundError:
            print(f"Background image not found at {bg_path}. Using solid color.")
            image = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 139, 255))  # Dark blue fallback
    
    # Ensure image is in RGBA mode
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    # Create a working canvas with alpha channel for title
    title_canvas = Image.new('RGBA', (WIDTH, HEIGHT))
    title_draw = ImageDraw.Draw(title_canvas)
    
    # Create a separate canvas for subtitles
    subtitle_canvas = Image.new('RGBA', (WIDTH, HEIGHT))
    subtitle_draw = ImageDraw.Draw(subtitle_canvas)
    
    # Calculate appropriate font size for title
    font_path = get_asset_path(os.path.join('assets', 'fonts', 'woodblock.otf'))
    max_width = WIDTH * 0.8  # Allow 80% of image width for text
    title_font_size = state['title_font_size']  # Use exact font size specified
    
    # Load fonts with anti-aliasing
    try:
        title_font = ImageFont.truetype(font_path, title_font_size)
    except:
        print("Woodblock font not found. Using default font for title.")
        title_font = ImageFont.load_default()
        title_font.size = title_font_size
    
    try:
        subtitle_font = ImageFont.truetype(
            get_asset_path(os.path.join('assets', 'fonts', 'futura-medium.ttf')), 
            state['subtitle_font_size']
        )
    except:
        print("Futura font not found. Using default font for subtitles.")
        subtitle_font = ImageFont.load_default()
        subtitle_font.size = state['subtitle_font_size']
    
    # Convert color to RGBA
    title_color = hex_to_rgba(state['color'])
    outline_color = hex_to_rgba(state['outline_color'])
    
    # Render main title with outline (lossless)
    title = state['text']
    bbox = title_draw.textbbox((0, 0), title, font=title_font)
    title_width = bbox[2] - bbox[0]
    title_height = bbox[3] - bbox[1]
    position = (WIDTH // 2 - title_width // 2, HEIGHT // 2 - title_height // 2)
    
    # Create outline by drawing multiple offset versions
    if state['outline'] > 0:
        outline_size = state['outline']
        for x in range(-outline_size, outline_size + 1, max(1, outline_size//3)):
            for y in range(-outline_size, outline_size + 1, max(1, outline_size//3)):
                if x == 0 and y == 0:
                    continue  # Skip the center position
                title_draw.text(
                    (position[0] + x, position[1] + y),
                    title,
                    fill=outline_color,
                    font=title_font,
                    anchor="lt"
                )
    
    # Draw main text on title canvas
    title_draw.text(
        position,
        title,
        fill=title_color,
        font=title_font,
        anchor="lt"
    )
    
    # Draw subtitles if enabled on subtitle canvas
    if state['show_credits']:
        # Small subtitle
        small_sub = state['small_subtitle']
        small_bbox = subtitle_draw.textbbox((0, 0), small_sub, font=subtitle_font)
        small_width = small_bbox[2] - small_bbox[0]
        small_height = small_bbox[3] - small_bbox[1]
        
        subtitle_draw.text(
            (WIDTH // 2 - small_width // 2, position[1] + title_height * 0.8 + 80),
            small_sub,
            fill=title_color if state.get('theme') == 'evil' else (255, 255, 255, 255),  # Use title color in evil mode
            font=subtitle_font,
            anchor="lt"
        )
        
        # Main subtitle
        sub = state['subtitle']
        sub_bbox = subtitle_draw.textbbox((0, 0), sub, font=subtitle_font)
        sub_width = sub_bbox[2] - sub_bbox[0]
        
        subtitle_draw.text(
            (WIDTH // 2 - sub_width // 2, position[1] + title_height * 0.8 + small_height * 1.5 + 90),
            sub,
            fill=title_color if state.get('theme') == 'evil' else (255, 255, 255, 255),  # Use title color in evil mode
            font=subtitle_font,
            anchor="lt"
        )
    
    # Apply perspective transformation to the title layer only
    width, height = title_canvas.size
    # Define the perspective points (bottom wider, top narrower)
    # Original corners
    top_left = (0, 0)
    top_right = (width, 0)
    bottom_left = (0, height)
    bottom_right = (width, height)
    
    # New corners with perspective
    perspective_top_left = (width * 0.1, 0)  # Move top left inward
    perspective_top_right = (width * 0.9, 0)  # Move top right inward
    perspective_bottom_left = (0, height)  # Keep bottom left
    perspective_bottom_right = (width, height)  # Keep bottom right
    
    # Calculate the perspective transform
    coeffs = find_coeffs(
        [perspective_top_left, perspective_top_right, perspective_bottom_left, perspective_bottom_right],
        [top_left, top_right, bottom_left, bottom_right]
    )
    
    # Apply the perspective transform to the title layer only
    title_canvas = title_canvas.transform(
        title_canvas.size,
        Image.Transform.PERSPECTIVE,
        coeffs,
        Image.Resampling.BICUBIC
    )
    
    # Composite the layers onto the background (lossless operation)
    if image.mode == 'RGB':
        image = image.convert('RGBA')
    # First composite the title
    final_image = Image.alpha_composite(image, title_canvas)
    # Then composite the subtitles
    final_image = Image.alpha_composite(final_image, subtitle_canvas)
    
    # Add blood effect overlay if specified (as the final step)
    blood_level = state.get('blood_level')
    if blood_level is not None and 1 <= blood_level <= 5:
        try:
            fx_path = get_asset_path(os.path.join('assets', 'fx', f'level{blood_level}.png'))
            overlay = Image.open(fx_path).convert('RGBA')
            overlay = overlay.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
            
            # Create a copy of the original image
            original_image = final_image.copy()
            
            # Create the multiply effect
            multiply_effect = apply_multiply(original_image, overlay)
            
            # Composite the multiply effect on top of the original
            final_image = Image.alpha_composite(original_image, multiply_effect)
        except FileNotFoundError:
            print(f"Blood effect overlay not found at {fx_path}")
    
    # Save as lossless PNG
    final_image.save(output_path, format='PNG', compress_level=0)
    print(f"Lossless title card saved to {output_path}")

def find_coeffs(pa, pb):
    """Find coefficients for perspective transform"""
    matrix = []
    for p1, p2 in zip(pa, pb):
        matrix.append([p1[0], p1[1], 1, 0, 0, 0, -p2[0]*p1[0], -p2[0]*p1[1]])
        matrix.append([0, 0, 0, p1[0], p1[1], 1, -p2[1]*p1[0], -p2[1]*p1[1]])
    
    A = np.matrix(matrix, dtype=np.float64)
    B = np.array(pb).reshape(8)
    
    res = np.dot(np.linalg.inv(A.T * A) * A.T, B)
    return np.array(res).reshape(8)

def calculate_font_size(text: str, font_path: str, max_width: int, initial_size: int) -> int:
    """Calculate the appropriate font size to fit text within max_width"""
    font_size = initial_size
    while True:
        try:
            font = ImageFont.truetype(font_path, font_size)
        except:
            font = ImageFont.load_default()
            font.size = font_size
            
        # Create a temporary image to measure text
        temp_image = Image.new('RGBA', (1, 1))
        temp_draw = ImageDraw.Draw(temp_image)
        bbox = temp_draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        
        if text_width <= max_width or font_size <= 20:  # Don't go smaller than 20px
            break
            
        # Reduce font size by 10% each iteration
        font_size = int(font_size * 0.9)
    
    return font_size

def hex_to_rgba(hex_color: str, alpha: int = 255):
    """Convert hex color to RGBA tuple"""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join([c * 2 for c in hex_color])
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4)) + (alpha,)

def apply_multiply(background, overlay):
    """Apply multiply blend mode using direct numpy multiplication"""
    # Convert images to numpy arrays and normalize to 0-1 range
    background_arr = np.array(background).astype(float) / 255.0
    overlay_arr = np.array(overlay).astype(float) / 255.0
    
    # Extract alpha channels
    background_alpha = background_arr[:, :, 3]
    overlay_alpha = overlay_arr[:, :, 3]
    
    # Apply multiply to RGB channels
    blended = background_arr[:, :, :3] * overlay_arr[:, :, :3]
    
    # Combine with alpha channels
    result = np.zeros_like(background_arr)
    result[:, :, :3] = blended
    result[:, :, 3] = overlay_alpha  # Use overlay's alpha
    
    # Convert back to 0-255 range and PIL Image
    return Image.fromarray((result * 255).astype(np.uint8))

def main():
    parser = argparse.ArgumentParser(
        description='Generate a title card with customizable text, colors, and effects.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        usage='%(prog)s "TITLE" [options]'
    )
    
    # Text options
    parser.add_argument('text', type=str,
                      help='Main title text (required)')
    parser.add_argument('--subtitle', type=str, default='Robert Kirkman, Cory Walker, & Ryan Ottley',
                      help='Main subtitle text')
    parser.add_argument('--small-subtitle', type=str, default='BASED ON THE COMIC BOOK BY',
                      help='Small subtitle text')
    
    # Font options
    parser.add_argument('--title-font-size', type=int, default=470,
                      help='Font size for the main title')
    parser.add_argument('--subtitle-font-size', type=int, default=40,
                      help='Font size for the subtitles')
    
    # Color options
    parser.add_argument('--color', type=str, default='#ebed00',
                      help='Text color in hex format (e.g., #ebed00)')
    parser.add_argument('--outline-color', type=str, default='#000000',
                      help='Outline color in hex format (e.g., #000000)')
    parser.add_argument('--outline', type=int, default=0,
                      help='Outline size in pixels')
    
    # Theme options
    parser.add_argument('--theme', type=str, choices=['evil', 'blood'],
                      help='Theme to use for the title card')
    parser.add_argument('--blood', type=int, choices=range(1, 6), metavar='[1-5]',
                      help='Add blood effect overlay (1-5)')
    
    # Background options
    parser.add_argument('--background', type=str, default='blue.jpg',
                      help='Background image filename (must be in assets/background/)')
    
    # Output options
    parser.add_argument('--output', type=str,
                      help='Output filename (defaults to TITLE.png)')
    parser.add_argument('--show-credits', '--credits', action='store_true',
                      help='Show subtitle credits')
    
    args = parser.parse_args()
    
    # Use the text as the output filename if not specified
    output_file = args.output if args.output else f"{args.text.lower()}.png"
    
    # Convert args to EditorState
    state: EditorState = {
        "text": args.text,
        "color": "#a93238" if args.theme == 'blood' else "#2f3336" if args.theme == 'evil' else args.color,  # Blood red or dark gray or default
        "show_credits": args.show_credits,
        "background": f"url('/background/{args.background}')",
        "title_font_size": args.title_font_size,  # Keep the same font size regardless of mode
        "subtitle_font_size": args.subtitle_font_size,  # Keep the same font size regardless of mode
        "outline": args.outline,
        "outline_color": args.outline_color,
        "small_subtitle": args.small_subtitle,
        "subtitle": args.subtitle,
        "theme": args.theme,
        "blood_level": args.blood
    }
    
    # Generate the title card
    generate_title_card(state, output_file)

if __name__ == "__main__":
    main()