import os
import requests
from io import BytesIO
import numpy as np
from PIL import Image
import rasterio
from rasterio.transform import from_bounds
import mercantile
from pathlib import Path

# Settings
Z_LEVEL = 18
TILE_GRID_SIZE = 8  # 8x8 tiles = 2048x2048 pixels
TILE_SIZE = 256

# Esri World Imagery TMS URL
TMS_URL = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"

SCENES = {
    "urban_showcase_hero.tif": {
        "lat": 40.7128,  # Lower Manhattan (City Hall area)
        "lon": -74.0060,
    },
    "terrain_showcase_hero.tif": {
        "lat": 36.1000,  # Grand Canyon
        "lon": -112.1000,
    }
}

OUTPUT_DIR = Path("demo_assets")
OUTPUT_DIR.mkdir(exist_ok=True)

def fetch_and_stitch_tiles(lat, lon, filename):
    print(f"\n--- Sourcing {filename} ---")
    
    # 1. Find the center tile
    center_tile = mercantile.tile(lon, lat, Z_LEVEL)
    
    # 2. Calculate the top-left tile of the 8x8 grid
    # We want center_tile to be roughly in the middle, so subtract 4 from X and Y
    start_x = center_tile.x - (TILE_GRID_SIZE // 2)
    start_y = center_tile.y - (TILE_GRID_SIZE // 2)
    
    # 3. Calculate Overall Bounds in WGS84 (EPSG:4326)
    # Mercantile Y increases as you go South.
    top_left_bounds = mercantile.bounds(start_x, start_y, Z_LEVEL)
    bottom_right_bounds = mercantile.bounds(start_x + TILE_GRID_SIZE - 1, start_y + TILE_GRID_SIZE - 1, Z_LEVEL)
    
    west = top_left_bounds.west
    north = top_left_bounds.north
    east = bottom_right_bounds.east
    south = bottom_right_bounds.south
    
    print(f"Calculated Bounds (WGS84): West={west}, South={south}, East={east}, North={north}")
    
    # 4. Download and stitch tiles
    canvas = np.zeros((TILE_GRID_SIZE * TILE_SIZE, TILE_GRID_SIZE * TILE_SIZE, 3), dtype=np.uint8)
    
    for row in range(TILE_GRID_SIZE):
        for col in range(TILE_GRID_SIZE):
            tx = start_x + col
            ty = start_y + row
            
            url = TMS_URL.format(z=Z_LEVEL, y=ty, x=tx)
            
            # Simple retry mechanism
            for _ in range(3):
                try:
                    resp = requests.get(url, timeout=10)
                    resp.raise_for_status()
                    img = Image.open(BytesIO(resp.content)).convert("RGB")
                    img_arr = np.array(img)
                    
                    # Place in canvas
                    y_pixel = row * TILE_SIZE
                    x_pixel = col * TILE_SIZE
                    canvas[y_pixel:y_pixel+TILE_SIZE, x_pixel:x_pixel+TILE_SIZE, :] = img_arr
                    break
                except Exception as e:
                    print(f"Error fetching tile {tx},{ty}: {e}")
                    img_arr = np.zeros((256,256,3), dtype=np.uint8) # Fallback to black tile
            
            print(f"Downloaded tile {row * TILE_GRID_SIZE + col + 1}/{TILE_GRID_SIZE*TILE_GRID_SIZE}", end="\r")
            
    print("\nStitching complete. Saving GeoTIFF...")
    
    # 5. Write GeoTIFF with rasterio
    transform = from_bounds(west, south, east, north, canvas.shape[1], canvas.shape[0])
    
    out_path = OUTPUT_DIR / filename
    
    with rasterio.open(
        out_path,
        'w',
        driver='GTiff',
        height=canvas.shape[0],
        width=canvas.shape[1],
        count=3,
        dtype=canvas.dtype,
        crs='EPSG:4326',
        transform=transform,
    ) as dst:
        # rasterio writes bands as (band, height, width)
        # canvas is (height, width, RGB)
        for i in range(3):
            dst.write(canvas[:, :, i], i + 1)
            
    print(f"Saved successfully to {out_path} (Size: {canvas.shape}, {out_path.stat().st_size / 1e6:.2f} MB)")


if __name__ == "__main__":
    for filename, coords in SCENES.items():
        fetch_and_stitch_tiles(coords["lat"], coords["lon"], filename)
        
    print("\nAll Hero Images sourced and prepared!")
