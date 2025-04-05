# Now You can Be Invisible too

A Python script to generate Invincible title cards with customizable text, colors, and effects. Perfect for creating title screens, thumbnails, or promotional images.

## Features

- Customizable title text with automatic font size adjustment
- Optional subtitles with credits
- Multiple background options
- Text outline and color customization
- Special effects (glitch, distort, shadow)
- Perspective transformation for the main title
- Lossless PNG output

## Requirements

- Python 3.x
- Pillow (PIL)
- NumPy

## Installation

1. Clone this repository:
```bash
git clone https://github.com/glitchmill/insoluble-py.git
cd title-card-generator
```

2. Install the required packages:
```bash
pip install -r requirements.txt
```

## Usage

Basic usage:
```bash
python app.py "YOUR TITLE"
```

This will generate a title card with your text and save it as `your-title.png`.

### Options

- `--subtitle TEXT`: Set the main subtitle (default: "Robert Kirkman, Cory Walker, & Ryan Ottley")
- `--small-subtitle TEXT`: Set the small subtitle (default: "BASED ON THE COMIC BOOK BY")
- `--title-font-size SIZE`: Set the initial title font size (default: 300)
- `--subtitle-font-size SIZE`: Set the subtitle font size (default: 30)
- `--color HEX`: Set the text color in hex format (default: "#ebed00")
- `--outline-color HEX`: Set the outline color in hex format (default: "#000000")
- `--outline SIZE`: Set the outline size in pixels (default: 0)
- `--background FILE`: Set the background image (must be in assets/background/)
- `--effect EFFECT`: Apply a special effect (choices: glitch, distort, shadow)
- `--output FILE`: Specify a custom output filename
- `--show-credits`: Show subtitle credits

### Examples

1. Basic title card:
```bash
python app.py "Invisible"
```

2. Title card with subtitles and custom colors:
```bash
python app.py "The Walking Dead" --show-credits --color "#ff0000" --outline 5
```

3. Title card with special effect:
```bash
python app.py "Invincible" --effect glitch --background red.jpg
```

## File Structure

```
.
├── app.py                 # Main script
├── assets/
│   ├── background/        # Background images
│   └── fonts/            # Font files
└── requirements.txt       # Python dependencies
```

## Notes

- The script automatically adjusts the font size if the title is too long
- Background images should be placed in the `assets/background/` directory
- Custom fonts should be placed in the `assets/fonts/` directory
- Output files are saved as lossless PNGs

## License

MIT License
