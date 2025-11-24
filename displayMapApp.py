import folium
from folium.plugins import Draw
from IPython.display import display, HTML

# Check if data from Part 1 is available
try:
    bounds = global_bounds
    image_data_url = global_image_data_url
    jgw_params = global_jgw_params
except NameError:
    print("Error: Please run Part 1 (File Upload and Georeferencing) first.")
    raise
    
print("1. Creating interactive map...")

# Determine the center of the map from the calculated bounds
center_y = (bounds[0][0] + bounds[1][0]) / 2
center_x = (bounds[0][1] + bounds[1][1]) / 2

# Create a Folium map instance
m = folium.Map(
    location=[center_y, center_x], 
    zoom_start=12, 
    tiles=None, # Start with no tiles/blank background
    crs='Simple', # Crucial: Use Simple CRS for planar coordinates (meters)
    width='100%',
    height='500px'
)

# Add a gray background to the map to see the drawing tools better
folium.TileLayer(
    'cartodbdarkmatter', 
    name='Background', 
    opacity=0.2, # Low opacity to ensure the image is prominent
    overlay=True,
    control=False
).add_to(m)

# Add the Image Overlay using the calculated world bounds
img_overlay = folium.raster_layers.ImageOverlay(
    name='Georeferenced Map',
    image=image_data_url,
    bounds=bounds,
    opacity=1.0,
    zindex=10, # Ensure the image is on top of the background tile
).add_to(m)

# Fit the map view precisely to the image bounds
m.fit_bounds(bounds)

# Add the Draw Control plugin
draw = Draw(
    export=False, 
    position='topleft',
    draw_options={
        'polyline': False, 
        'marker': False, 
        'circlemarker': False, 
        'circle': False, 
        'rectangle': False,
        'polygon': {'shapeOptions': {'color': '#4c1d95', 'fillColor': '#4c1d95', 'fillOpacity': 0.5}} # Custom color
    },
    edit_options={'edit': True, 'remove': True}
).add_to(m)

# --- JAVASCRIPT SNIPPET TO CAPTURE DRAWN SHAPE DATA ---
# This script runs in the browser when the map is displayed.

js_capture = """
    <script>
        var map_id = '{map_id}';
        var map = window.document.getElementById(map_id)._leaflet_map;
        
        // Define a global variable to store the last drawn coordinates
        window.lastDrawnCoords = null;

        map.on(L.Draw.Event.CREATED, function (e) {
            var type = e.layerType,
                layer = e.layer;

            if (type === 'polygon') {
                // Get the coordinates in the map's current CRS (which are the JGW-based meters)
                // Coordinates come back as [Lat/Y, Lng/X] pairs (Northing, Easting)
                var latlngs = layer.getLatLngs()[0];
                var coords = latlngs.map(function(ll) {
                    return [ll.lng, ll.lat]; // Store as [X, Y] (Easting, Northing) as expected by Shapely
                });
                
                // Store the coordinates globally so the next Python cell can access them
                window.lastDrawnCoords = JSON.stringify(coords);

                layer.bindPopup('Shape Drawn. Run Part 3 to calculate area.').openPopup();

                // Clear any previous shapes for simplicity, keep only the latest one
                map.eachLayer(function(l) {
                    // Check if it's a feature layer (not the map background or image overlay)
                    if (l instanceof L.Path && l._leaflet_id !== layer._leaflet_id) {
                        map.removeLayer(l);
                    }
                });
            }
        });
    </script>
""".replace('{map_id}', m.get_name())

# Display the map and the hidden JavaScript code
display(m, HTML(js_capture))

print("\nPart 2 complete. The interactive map is displayed above.")
print("Use the Polygon tool (the first icon on the left of the map) to draw a boundary on your map image.")
print("Once drawn, proceed to run Part 3.")
