import json
import geopandas as gpd
import pandas as pd
from tqdm import tqdm
from guaraguao import Sentinel2
import shapely 
from shapely import affinity
from pathlib import Path
import glob
import rioxarray as rxr
import numpy as np
from rasterio.features import geometry_mask


def get_bbox(
        point:shapely.Point, 
        x_shift:float, 
        y_shift:float
    ) -> json:
    """
    Generates a feature collection with a bounding box
    that represents the area of the satellite image
    """
    shifted_p = affinity.translate(point ,xoff=-x_shift, yoff= -y_shift)
    y_max = shifted_p.xy[1][0]
    x_min = shifted_p.xy[0][0]
    x_max = x_min + 2*x_shift
    y_min = y_max + 2*y_shift
    
    bbox = shapely.box(ymax=y_max, xmin=x_min, ymin=y_min, xmax=x_max)
    polygon_geojson = json.loads(shapely.to_geojson(bbox))
    return {
              "type": "FeatureCollection",
              "features": [
                {
                  "type": "Feature",
                  "properties": {},
                  "geometry": polygon_geojson
                }
            ]
        }

def crop_to_minimum(arrays):
    """Crop all arrays to the minimum dimensions across all arrays"""
    # Find minimum dimensions
    min_dims = []
    for dim in range(len(arrays[0].shape)):
        min_dim = min(arr.shape[dim] for arr in arrays)
        min_dims.append(min_dim)
    
    # Crop all arrays
    standardized = []
    for arr in arrays:
        slices = tuple(slice(0, min_dim) for min_dim in min_dims)
        standardized.append(arr[slices])
    
    return standardized
