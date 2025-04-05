import os
from PIL import Image, ImageDraw, ImageFont, ImageOps
from typing import Optional, Literal, TypedDict
import numpy as np

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

def generate_title_card(state: EditorState, output_path: str = "output.png"):
    # Load background image (lossless PNG)
    bg_path = os.path.join('assets', 'background', 'blue.jpg')  # Prefer PNG background
    try:
        if bg_path.endswith('.png'):
            image = Image.open(bg_path).convert('RGBA')
        else:
            image = Image.open(bg_path).convert('RGB')
    except FileNotFoundError:
        print(f"Background image not found at {bg_path}. Using solid color.")
        image = Image.new('RGBA', (1920, 1080), (0, 0, 139, 255))  # Dark blue fallback
    
    # Create a working canvas with alpha channel
    canvas = Image.new('RGBA', image.size)
    draw = ImageDraw.Draw(canvas)
    
    # Load fonts with anti-aliasing
    try:
        title_font = ImageFont.truetype(
            os.path.join('assets', 'fonts', 'woodblock.otf'), 
            state['title_font_size']
        )
    except:
        print("Woodblock font not found. Using default font for title.")
        title_font = ImageFont.load_default()
        title_font.size = state['title_font_size']
    
    try:
        subtitle_font = ImageFont.truetype(
            os.path.join('assets', 'fonts', 'futura-medium.ttf'), 
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
    bbox = draw.textbbox((0, 0), title, font=title_font)
    title_width = bbox[2] - bbox[0]
    title_height = bbox[3] - bbox[1]
    position = (image.width // 2 - title_width // 2, image.height // 2 - title_height // 2)
    
    # Create outline by drawing multiple offset versions
    if state['outline'] > 0:
        outline_size = state['outline']
        for x in range(-outline_size, outline_size + 1, max(1, outline_size//3)):
            for y in range(-outline_size, outline_size + 1, max(1, outline_size//3)):
                if x == 0 and y == 0:
                    continue  # Skip the center position
                draw.text(
                    (position[0] + x, position[1] + y),
                    title,
                    fill=outline_color,
                    font=title_font,
                    anchor="lt"
                )
    
    # Draw main text
    draw.text(
        position,
        title,
        fill=title_color,
        font=title_font,
        anchor="lt"
    )
    
    # Draw subtitles if enabled
    if state['show_credits']:
        # Small subtitle
        small_sub = state['small_subtitle']
        small_bbox = draw.textbbox((0, 0), small_sub, font=subtitle_font)
        small_width = small_bbox[2] - small_bbox[0]
        small_height = small_bbox[3] - small_bbox[1]
        
        draw.text(
            (image.width // 2 - small_width // 2, position[1] + title_height * 0.8),
            small_sub,
            fill=(255, 255, 255, 255),  # White with full opacity
            font=subtitle_font,
            anchor="lt"
        )
        
        # Main subtitle
        sub = state['subtitle']
        sub_bbox = draw.textbbox((0, 0), sub, font=subtitle_font)
        sub_width = sub_bbox[2] - sub_bbox[0]
        
        draw.text(
            (image.width // 2 - sub_width // 2, position[1] + title_height * 0.8 + small_height * 1.5),
            sub,
            fill=(255, 255, 255, 255),  # White with full opacity
            font=subtitle_font,
            anchor="lt"
        )
    
    # Composite the text onto the background (lossless operation)
    if image.mode == 'RGB':
        image = image.convert('RGBA')
    final_image = Image.alpha_composite(image, canvas)
    
    # Apply effects in a lossless way when possible
    if state['effect']:
        final_image = apply_lossless_effect(final_image, state['effect'])
    
    # Save as lossless PNG
    final_image.save(output_path, format='PNG', compress_level=0)
    print(f"Lossless title card saved to {output_path}")

def hex_to_rgba(hex_color: str, alpha: int = 255):
    """Convert hex color to RGBA tuple"""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join([c * 2 for c in hex_color])
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4)) + (alpha,)

def apply_lossless_effect(image: Image.Image, effect_name: str) -> Image.Image:
    """Apply effects while maintaining lossless quality where possible"""
    if effect_name == 'glitch':
        # Convert to array for pixel manipulation
        arr = np.array(image)
        height, width = arr.shape[:2]
        
        # Create glitch by shifting channels
        glitch_arr = arr.copy()
        shift = width // 20
        glitch_arr[:, shift:, :3] = arr[:, :-shift, :3]  # Shift RGB channels
        glitch_arr[:, :shift, 3] = arr[:, -shift:, 3]    # Preserve alpha
        
        return Image.fromarray(glitch_arr)
    
    elif effect_name == 'shadow':
        # Create shadow with alpha channel
        shadow = Image.new('RGBA', image.size, (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow)
        
        # Draw a semi-transparent rectangle
        shadow_draw.rectangle(
            [50, 50, image.width-50, image.height-50],
            fill=(0, 0, 0, 50)  # 50/255 opacity
        )
        
        return Image.alpha_composite(image, shadow)
    
    elif effect_name == 'distort':
        # Wave distortion using numpy for precision
        arr = np.array(image)
        height, width = arr.shape[:2]
        
        # Create wave distortion
        x = np.arange(width)
        y = np.arange(height)
        xx, yy = np.meshgrid(x, y)
        
        # Apply sine wave distortion
        wave = np.sin(yy / 30) * 10
        distorted_x = np.clip(xx + wave.astype(int), 0, width-1)
        
        # Create new image with distortion
        distorted_arr = arr.copy()
        distorted_arr[yy, xx] = arr[yy, distorted_x]
        
        return Image.fromarray(distorted_arr)
    
    return image

if __name__ == "__main__":
    # Default state with lossless settings
    default_state: EditorState = {
        "text": "INSOLUBLE",
        "color": "#ebed00",
        "show_credits": False,
        "background": "url('/background/blue.jpg')",  # Prefer PNG background
        "title_font_size": 300,
        "subtitle_font_size": 30,
        "outline": 0,
        "outline_color": "#000000",
        "effect": None,
        "small_subtitle": "BASED ON THE COMIC BOOK BY",
        "subtitle": "Robert Kirkman, Cory Walker, & Ryan Ottley",
    }
    
    # Generate with default settings
    generate_title_card(default_state)
    
    # # Example of custom generation with effects
    # custom_state = default_state.copy()
    # custom_state.update({
    #     "text": "INVINCIBLE WAR",
    #     "color": "#ff0000",
    #     "title_font_size": 180,
    #     "outline": 15,
    #     "effect": "glitch"
    # })
    # generate_title_card(custom_state, "custom_output.png")