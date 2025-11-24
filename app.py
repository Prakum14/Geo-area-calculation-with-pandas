# -*- coding: utf-8 -*-
#
# Geographic Area Calculator - Core Logic Test (REVISED FOR NESTED ZIPS AND CRS FIX)
# This version recursively searches for the .shp file AND explicitly sets the 
# Coordinate Reference System (CRS) if the data is loaded as "naive."

# 1. Installation of required libraries
print("Installing required libraries (geopandas and dependencies)...")
!pip install geopandas fiona pyproj --quiet

import geopandas as gpd
import pandas as pd
import tempfile
import zipfile
import os
from google.colab import files # Used for file upload in Google Colab

print("\nLibraries installed and imported successfully.")

# --- Core Functions from app.py ---

def process_shapefile(uploaded_zip_path):
    """
    Handles the uploaded ZIP file path, extracts its contents, and reads the 
    shapefile into a GeoDataFrame. It ensures a CRS is set.
    """
    print(f"Processing ZIP file: {uploaded_zip_path}")
    
    # Create a temporary directory to extract files
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            # Unzip the file directly into the temp directory
            with zipfile.ZipFile(uploaded_zip_path, 'r') as zip_ref:
                zip_ref.extractall(tmpdir)
            
            # --- 1. ROBUST SEARCH FOR .shp FILE ---
            shp_path = None
            for dirpath, dirnames, filenames in os.walk(tmpdir):
                for filename in filenames:
                    if filename.endswith('.shp'):
                        shp_path = os.path.join(dirpath, filename)
                        print(f"Found shapefile at: {shp_path}")
                        break
                if shp_path:
                    break 

            if not shp_path:
                print("Error: Could not find a .shp file inside the ZIP archive.")
                return None

            # 2. Read the shapefile
            gdf = gpd.read_file(shp_path)
            
            # --- 3. FIX: Handle Naive CRS ---
            if gdf.crs is None:
                print("Warning: GeoDataFrame is 'naive' (missing CRS). Assuming EPSG:4326 (WGS 84).")
                # Most global/web data is WGS 84, which is a safe assumption for unprojected data.
                gdf.set_crs(epsg=4326, inplace=True)
            else:
                print(f"CRS detected: {gdf.crs}")
            
            print(f"Successfully loaded data with {len(gdf)} features.")
            return gdf
            
        except zipfile.BadZipFile:
            print("Error: The uploaded file is not a valid ZIP archive.")
            return None
        except Exception as e:
            print(f"An unexpected error occurred during processing: {e}")
            return None

def calculate_area(gdf, granularity_col):
    """
    Calculates the area in square kilometers for each unique entity
    defined by the selected granularity column.
    """
    print(f"\n--- Calculating areas based on the level: {granularity_col} ---")

    # 1. Re-project to a metric CRS (EPSG:3857) to enable area calculation in meters
    # This step will now succeed because we guaranteed that gdf has a CRS set (either from file or our default 4326).
    print("Re-projecting to metric CRS (EPSG:3857) for area calculation...")
    gdf_metric = gdf.to_crs(epsg=3857)
    
    # Calculate area in square meters and convert to square kilometers
    gdf_metric['area_sq_km'] = gdf_metric.geometry.area / 10**6
    
    # 2. Group the results by the chosen granularity column
    results = gdf_metric.groupby(granularity_col)['area_sq_km'].sum().reset_index()
    
    # 3. Format the result
    results.columns = ['Entity Name', 'Area (sq km)']
    results['Area (sq km)'] = results['Area (sq km)'].round(2)
    
    return results

# --- Main Execution Block ---

print("\n--- Start Execution ---\n")

# Use Colab's file upload widget
print("Please upload your zipped shapefile now.")
try:
    uploaded = files.upload() 
except Exception as e:
    print(f"Colab file upload failed: {e}. Are you sure you are running this in a Colab environment?")
    uploaded = {}

if not uploaded:
    print("No file was uploaded or upload failed. Please upload a ZIP file containing your shapefile.")
else:
    # Get the file name from the uploaded dictionary keys
    zip_file_name = list(uploaded.keys())[0]

    # Step 1: Process the shapefile
    gdf_data = process_shapefile(zip_file_name)

    if gdf_data is not None:
        
        # Step 2: Show available attribute columns for selection
        available_columns = [col for col in gdf_data.columns if col != 'geometry']
        print("\nAvailable Granularity Columns (Attribute Fields):")
        print(available_columns)

        # Heuristic to guess a good column:
        preferred_names = ['NAME_1', 'name', 'NAME', 'ADM1_EN', available_columns[0]]
        test_granularity_col = next((c for c in preferred_names if c in available_columns), None)

        if test_granularity_col:
            print(f"\n--- Testing Calculation with assumed Granularity: '{test_granularity_col}' ---")
            
            # Step 3: Perform the area calculation
            final_results = calculate_area(gdf_data, test_granularity_col)
            
            # Step 4: Display the final results
            print("\n--- Final Area Calculation Results (Top 10) ---")
            print(final_results.head(30).to_markdown(index=False))
            print(f"\nTotal entities calculated: {len(final_results)}")
        else:
            print("\nCould not find any suitable attribute columns to calculate area.")

