import os
import io
import numpy as np
import base64 # Import base64 for proper image encoding
from PIL import Image
from IPython.display import display, HTML
from google.colab import files

# --- 1. SETUP AND FILE UPLOAD ---
print("1. Installing required libraries...")
!pip install -qq folium Pillow numpy shapely

# Upload the JPG map image and the JGW world file.
print("\n2. Please upload your .jpg (map image) and .jgw (world file) now.")
uploaded = files.upload()

# --- 2. FILE IDENTIFICATION AND READING ---
jpg_content = None
jgw_content = None
jpg_filename = None

for name, content in uploaded.items():
    if name.lower().endswith(('.jpg', '.jpeg')):
        jpg_content = content
        jpg_filename = name
    elif name.lower().endswith('.jgw'):
        jgw_content = content

if not jpg_content or not jgw_content:
    # If files are missing, raise an error to stop execution
    raise FileNotFoundError("Error: Could not find both a .jpg and a .jgw file. Please try again.")
else:
    print(f"\nSuccess! JPG file '{jpg_filename}' and JGW file loaded.")

# --- 3. JGW PARSING AND BOUNDS CALCULATION ---

def parse_jgw(content):
    """Parses JGW content (6 lines) into the affine transformation matrix parameters."""
    content_str = content.decode('utf-8').strip().replace('\r\n', '\n')
    lines = content_str.split('\n')
    
    if len(lines) < 6:
        raise ValueError("JGW file must contain 6 numeric lines.")
        
    try:
        # JGW Standard Order: A, D, B, E, C, F
        params = {
            'A': float(lines[0].strip()), # Scale X
            'D': float(lines[1].strip()), # Rotation
            'B': float(lines[2].strip()), # Rotation
            'E': float(lines[3].strip()), # Scale Y (usually negative)
            'C': float(lines[4].strip()), # World X coordinate of center of top-left pixel
            'F': float(lines[5].strip()), # World Y coordinate of center of top-left pixel
        }
    except ValueError as e:
        raise ValueError(f"Could not parse numeric data from JGW file: {e}")
        
    return params

def pixel_to_world(x_pixel, y_pixel, params):
    """Converts pixel coordinates to world coordinates (X_world, Y_world)."""
    # JGW is based on the center of the pixel, so we add 0.5
    x_adj = x_pixel + 0.5
    y_adj = y_pixel + 0.5
    
    X_world = params['A'] * x_adj + params['B'] * y_adj + params['C']
    Y_world = params['D'] * x_adj + params['E'] * y_adj + params['F']
    
    # Return Y (Northing/Lat) first, then X (Easting/Lng) to match Leaflet/Folium convention for coordinates
    return Y_world, X_world

# Process the image and JGW data
try:
    img = Image.open(io.BytesIO(jpg_content))
    image_width, image_height = img.size
    jgw_params = parse_jgw(jgw_content)
    
    # Calculate the world coordinates of the four corners (0,0) and (width, height)
    TL_Y, TL_X = pixel_to_world(0, 0, jgw_params) # Top-Left (TL)
    BR_Y, BR_X = pixel_to_world(image_width, image_height, jgw_params) # Bottom-Right (BR)
    
    # Determine the actual bounding box corners for the image overlay
    min_X = min(TL_X, BR_X)
    max_X = max(TL_X, BR_X)
    min_Y = min(TL_Y, BR_Y)
    max_Y = max(TL_Y, BR_Y)

    # bounds = [[min_Y, min_X], [max_Y, max_X]] -> [[min_lat, min_lng], [max_lat, max_lng]]
    bounds = [[min_Y, min_X], [max_Y, max_X]]
    
    # **REVISED Base64 encoding:** Convert image bytes to standard Base64 string for the Data URL
    img_format = img.format if img.format else 'JPEG'
    encoded_string = base64.b64encode(jpg_content).decode('utf-8')
    image_data_url = f'data:image/{img_format.lower()};base64,{encoded_string}'

    # Store results in global variables for the next cell
    global global_bounds, global_image_data_url, global_jgw_params
    global_bounds = bounds
    global_image_data_url = image_data_url
    global_jgw_params = jgw_params
    
    print("\n--- Georeferencing Parameters ---")
    print(f"Image Dimensions: {image_width} x {image_height} pixels")
    print(f"World Bounding Box (Y/X meters): {global_bounds}")
    print("\nPart 1 complete. Run Part 2 to display the map.")
    
except Exception as e:
    print(f"\nFatal Error during processing: {e}")
    # Raise the exception to halt execution if a fatal error occurs
    raise
