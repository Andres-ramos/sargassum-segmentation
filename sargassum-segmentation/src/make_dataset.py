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
import logging
from src.utils import get_bbox
from src.utils import crop_to_minimum


def main(annotation_path: str) -> None:
    """
    Converts annotations in data/raw folder into tif and segmentation masks
    """
    cache_name="cache"
    cache_path = Path(f"data/external/{cache_name}")
    sentinel_client = Sentinel2(cache_path, collection="S2_HARMONIZED")

    raw_data_path = annotation_path / Path("raw")
    image_width = 0.009
    image_height = 0.009
    polygon_gdf= raw_json_to_polygon_gdf(
        input_filepath=raw_data_path, 
        sentinel_client=sentinel_client,
        image_width=image_width,
        image_height=image_height
    )
    # Convert polygon gdf into segmentation mask
    mask_path_list = []
    for path, polygon in zip(polygon_gdf["path"], polygon_gdf["geometry"]):
        raster_id = path.split("/")[-1].split(".")[0]
        data = rxr.open_rasterio(path)
        mask = geometry_mask(
            [polygon], 
            transform=data.rio.transform(),
            invert=True,  # True inside polygon, False outside
            out_shape=data.shape[-2:]  # (height, width)
        )
        # Convert from bool mask to int mask
        if mask.shape[0] > 201:
            mask = mask[:-1, :]
        if mask.shape[1] > 201:
            mask = mask[:, :-1]

        mask = mask * 1
        mask_path = annotation_path / Path(f"processed/segmentation/mask/{raster_id}.npy")
        np.save(mask_path, mask)
        mask_path_list.append(mask_path)

    polygon_gdf["mask_path"] = mask_path_list
    polygon_gdf.to_file(annotation_path / Path(f"processed/segmentation/polygon/"))

def raw_json_to_polygon_gdf(
        input_filepath: str, 
        sentinel_client: any, 
        image_width: float,
        image_height: float,
    ) -> gpd.GeoDataFrame:

    gdf = generate_polygon_df(input_filepath)
    gdf = download_images(gdf, sentinel_client, image_width, image_height)
    gdf.set_crs("4326")
    return gdf

def generate_polygon_df(annotations_folder:str) -> gpd.GeoDataFrame:
    """
    Converts raw json annotations to geopandas dataframe
    Input: annotations_folder - class_-date.json format 
    Output: geodataframe
    """
    gdfs = []
    # For each annotation fole
    for polygon_annotations in glob.glob(f"{str(annotations_folder)}/**.json"):
        # Extract class
        # TODO: Modularize so that data can be anywhere
        class_ = polygon_annotations.split(".")[0].split("/")[6].split("-")[0]
        # Load json file into geodataframe
        with open(polygon_annotations) as f:
            polygon_geojson = json.loads(f.read())
        gdf = gpd.GeoDataFrame.from_features(polygon_geojson)
        # Add class column
        gdf["class_"] = [class_]*len(gdf.index)
        gdfs.append(gdf)

    # Returns geodataframe
    return gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True))


def download_images(
        gdf: gpd.GeoDataFrame, 
        sentinel_client: any, 
        image_width: float, 
        image_height: float
    ) -> gpd.GeoDataFrame:
    """
    Downloads images 
    """
    #TODO: Download all the metadata
    paths = []
    space_craft_name_list = []
    mean_solar_asimuth_angle_list = []
    mean_solar_zenith_angle_list = []
    hour_list = []

    #For each polygon in gdf, downloads image and metadata and adds it to geodataframe 
    for poly,date in tqdm(zip(gdf["geometry"], gdf["date"])):
        
        bbox = get_bbox(poly.centroid, image_width, image_height)

        try :
            image = sentinel_client.fetch_image(bbox, date)
            paths.append(image.attrs["image_path"])
            if "properties" in image.attrs.keys():

                val = (image.attrs["properties"]["SPACECRAFT_NAME"] if 'SPACECRAFT_NAME' in image.attrs["properties"] else "")
                space_craft_name_list.append(val)

                val = (image.attrs["properties"]["MEAN_SOLAR_AZIMUTH_ANGLE"] if 'MEAN_SOLAR_AZIMUTH_ANGLE' in image.attrs["properties"] else "")
                mean_solar_asimuth_angle_list.append(val)

                val = (image.attrs["properties"]["MEAN_SOLAR_ZENITH_ANGLE"] if 'MEAN_SOLAR_ZENITH_ANGLE' in image.attrs["properties"] else "")
                mean_solar_zenith_angle_list.append(val)

                val = (image.attrs["properties"]["system:time_start"] if 'system:time_start' in image.attrs["properties"] else "")
                hour_list.append(val)

        # TODO: Better error handling
        # TODO: Remove prints
        except Exception as e:
            print(e)
            print("download failed")
            paths.append("")
            space_craft_name_list.append("")
            mean_solar_asimuth_angle_list.append("")
            mean_solar_zenith_angle_list.append("")
            hour_list.append("")

    gdf["spacecraft_name"] = space_craft_name_list
    gdf["azimuth_angle"] = mean_solar_asimuth_angle_list
    gdf["zenith_angle"] = mean_solar_zenith_angle_list
    gdf["time"] = hour_list
    gdf["path"] = paths
    return gdf

if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    project_dir = Path(__file__).resolve().parents[2]
    annotation_path = project_dir / Path("data")

    main(annotation_path)


