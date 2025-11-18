import streamlit as st
import pandas as pd
import geopandas as gpd
from shapely.geometry import shape
from fastkml import kml, geometry
from io import BytesIO
import fiona
# --- NEW: Import the classification function from the ML module ---
from ML.classifier import classify_region_ml

# --- Configuration ---
st.set_page_config(
    page_title="Geospatial Area Calculator",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Set an appropriate Equal-Area projection for accurate area measurement (Mollweide)
# For local or specific regions, a UTM or similar localized projection would be better.
EQUAL_AREA_CRS = 'ESRI:54009' 
DEFAULT_CRS = 'EPSG:4326' # WGS 84 used by KML

# --- Core Geospatial Logic ---

def parse_kml_to_geodataframe(uploaded_file):
    """Parses KML file, extracts geometries and properties, and creates a GeoDataFrame."""
    
    st.info("Parsing KML file and extracting geometries...")
    
    # KML parsing using fastkml (safer for complex KML structures)
    k = kml.KML()
    k.from_string(uploaded_file.getvalue())
    
    features = []
    
    # Helper to recursively extract features (placemarks)
    def extract_features(element):
        if isinstance(element, kml.Placemark):
            # Extract basic geometry and properties
            if element.geometry and isinstance(element.geometry, (geometry.Polygon, geometry.MultiPolygon)):
                geom = shape(element.geometry)
                
                # Check for properties (use name/description if present)
                props = {
                    'name': element.name if element.name else f"Region-{len(features) + 1}",
                    'description': element.description
                }
                features.append({'geometry': geom, **props})
        
        if hasattr(element, 'features'):
            for feature in element.features():
                extract_features(feature)

    extract_features(k.features())
    
    if not features:
        st.error("No valid Polygon or MultiPolygon geometries found in the KML file.")
        return None

    # Create GeoDataFrame
    gdf = gpd.GeoDataFrame(features, crs=DEFAULT_CRS)
    return gdf

def analyze_area(gdf):
    """Calculates area for each region and sums the total area per class."""
    
    # 1. Reproject for accurate area calculation
    st.info(f"Reprojecting geometries to Equal-Area CRS ({EQUAL_AREA_CRS}) for accurate area calculation.")
    gdf_proj = gdf.to_crs(EQUAL_AREA_CRS)
    
    # 2. Calculate Area (in square meters, then convert to square kilometers)
    gdf_proj['area_sq_m'] = gdf_proj.geometry.area
    gdf_proj['Area (sq km)'] = gdf_proj['area_sq_m'] / 1_000_000
    
    # 3. Classify regions using the imported ML function
    # NOTE: We now use 'classify_region_ml'
    gdf_proj['Class'] = gdf_proj.apply(
        lambda row: classify_region_ml(row['Area (sq km)'], row['name']), 
        axis=1
    )
    
    # Keep only relevant columns for output
    result_df = gdf_proj[['name', 'Class', 'Area (sq km)']].copy()
    
    # 4. Calculate Summary Area
    summary_df = result_df.groupby('Class')['Area (sq km)'].sum().reset_index()
    summary_df.columns = ['Class', 'Total Area (sq km)']
    summary_df['Total Area (sq km)'] = summary_df['Total Area (sq km)'].round(2)
    
    result_df['Area (sq km)'] = result_df['Area (sq km)'].round(4)
    
    return result_df, summary_df


# --- Streamlit UI Layout ---

def main():
    st.title("🗺️ KML Geospatial Area Analysis Tool")
    st.markdown("Upload a KML file with demarcated regions to calculate individual and summed areas by inferred class (State, District, City, Muhalla).")
    
    # Inform the user about the current classification method
    st.warning(
        "**Currently using simple area thresholds for classification.** "
        "This tool is ready for you to integrate your sophisticated **ML model** into `ML/classifier.py`!"
    )
    
    st.divider()

    uploaded_file = st.file_uploader(
        "Upload KML File (e.g., map.kml or map.zip containing KML)", 
        type=['kml', 'zip'] # KML files are often packaged in KMZ (which is a zip)
    )

    if uploaded_file is not None:
        try:
            # Need to handle case where KMZ is uploaded (which is a zip file)
            file_name = uploaded_file.name
            if file_name.lower().endswith('.zip') or file_name.lower().endswith('.kmz'):
                 # fiona can sometimes handle KMZ/zipped shapefiles directly, but 
                 # fastkml expects the unzipped KML content. Using BytesIO for fastkml.
                 st.error("KMZ/ZIP file handling needs more complex extraction logic. Please provide the raw `.kml` file for best results with the current prototype.")
                 return

            gdf = parse_kml_to_geodataframe(uploaded_file)
            
            if gdf is not None and not gdf.empty:
                individual_areas_df, total_areas_df = analyze_area(gdf)
                
                # --- Display Results ---
                
                st.header("Results Summary")
                st.subheader("Total Area by Class")
                st.dataframe(total_areas_df, use_container_width=True, hide_index=True)
                
                
                st.subheader("Individual Region Area Details")
                st.markdown("This table lists the calculated area and the assigned class for each individual region.")
                st.dataframe(individual_areas_df, use_container_width=True, hide_index=True)

        except fiona.errors.DriverError as e:
             st.error(f"Error reading the uploaded file. Please ensure it is a valid KML file. Details: {e}")
        except Exception as e:
            st.error(f"An unexpected error occurred during processing. Error: {e}")
            st.code(str(e))


if __name__ == '__main__':
    main()
```
eof

---

## **Final Folder Structure Check**

Before running, make sure your project directory looks like this:

```
project-area-analyzer/
├── app.py             <-- (The updated code above)
├── requirements.txt
├── README.md
└── ML/
    └── classifier.py  <-- (The new file above)
