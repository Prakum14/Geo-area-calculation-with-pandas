from shapely.geometry import Polygon
import json
from google.colab import output 
from IPython.display import display

# --- 1. COORDINATE RETRIEVAL FROM JAVASCRIPT ---

print("1. Attempting to retrieve coordinates from the drawn shape...")

# This JavaScript snippet accesses the global variable set by the Folium map in Part 2.
js_get_coords = """
    (function() {
        // Returns the JSON string of coordinates, or null if nothing was drawn
        return window.lastDrawnCoords; 
    })();
"""

# Use output.eval_js to reliably get the string result from the browser environment
# If the JS returns null, eval_js returns None, which is the source of your error.
try:
    raw_coords = output.eval_js(js_get_coords)
except Exception as e:
    print(f"Error retrieving data from map: {e}.")
    raw_coords = None # Default to None on any JS execution error

# --- 2. AREA CALCULATION ---

# Check explicitly for None, the string 'null' (which is sometimes returned by JS), or the empty list placeholder.
if raw_coords is None or raw_coords in ('null', '[]'):
    print("\nError: No valid coordinates were retrieved. Please ensure you performed the following steps:")
    print("1. Run Part 2.")
    print("2. Use the Polygon tool (first icon on the left of the map) to draw a shape.")
    print("3. **Complete the polygon** by clicking on the starting point again.")
    print("4. Only then, run Part 3.")
else:
    try:
        # The coordinates are returned as a JSON string, so we parse it.
        # Coords are in [X, Y] (Easting, Northing in meters)
        coords = json.loads(raw_coords)

        if not coords:
            print("Error: Coordinates list is empty. Was the polygon closed correctly?")
        else:
            # Create a Shapely Polygon. 
            polygon = Polygon(coords)
            area_sq_meters = polygon.area
            
            # --- 3. RESULTS DISPLAY ---
            
            def format_area(area_m2):
                """Formats the area into appropriate units (m², ha, km²)."""
                if area_m2 >= 1000000:
                    return f"{area_m2 / 1000000:.4f} km² (Square Kilometers)"
                elif area_m2 >= 10000:
                    return f"{area_m2 / 10000:.4f} ha (Hectares)"
                else:
                    return f"{area_m2:.2f} m² (Square Meters)"

            print("\n--- Area Calculation Results ---")
            print(f"Planar Area: {format_area(area_sq_meters)}")
            print("\nCalculation complete.")

    except json.JSONDecodeError:
        print("Error: Failed to parse JSON coordinates. The retrieved data format was corrupted.")
    except Exception as e:
        # This should no longer be hit by the NoneType error, but is kept for general robustness.
        print(f"An unexpected error occurred during calculation: {e}")
