import rasterio
import geopandas as gpd
import numpy as np
import os
from PIL import Image
from rasterio.mask import mask
from shapely.geometry import box

class ArcGIS_Overlapper:
    def __init__(self, tif_path: str, overlay_png_path: str, shp_path: str, output_path: str):
        self.tif_path = tif_path
        self.overlay_png_path = overlay_png_path
        self.shp_path = shp_path
        self.output_path = output_path
        self.tif_data = None
        self.overlay_png_data = None
        self.shp_data = None

    def load_tif(self):
        self.tif_data = rasterio.open(self.tif_path)

    def load_png(self):
        self.overlay_png_data = Image.open(self.overlay_png_path).convert('L')

    def load_shp(self):
        self.shp_data = gpd.read_file(self.shp_path)

    def process_and_save_tif(self):
        if self.tif_data is None or self.shp_data is None or self.overlay_png_data is None:
            raise ValueError()

        minx, miny, maxx, maxy = 30, -20, 38, -8
        bbox = gpd.GeoDataFrame({'geometry': [box(minx, miny, maxx, maxy)]}, crs=self.shp_data.crs)

        out_image, out_transform = mask(self.tif_data, bbox.geometry, crop=True)
        out_meta = self.tif_data.meta.copy()
        out_meta.update({"driver": "GTiff",
                         "height": out_image.shape[1],
                         "width": out_image.shape[2],
                         "transform": out_transform})

        overlay_array = np.array(self.overlay_png_data)
        overlay_resized = np.array(Image.fromarray(overlay_array).resize((out_image.shape[2], out_image.shape[1]), Image.NEAREST))

        combined_image = np.zeros_like(out_image, dtype=np.uint8)
        combined_image[:, overlay_resized != 255] = out_image[:, overlay_resized != 255]
        combined_image[:, overlay_resized != 255] = overlay_resized[overlay_resized != 255]

        output_dir = os.path.dirname(self.output_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        with rasterio.open(self.output_path, "w", **out_meta) as dest:
            dest.write(combined_image)

if __name__ == "__main__":
    visualizer = ArcGIS_Overlapper(
        tif_path='./tif/Extract_Basi3.tif',
        overlay_png_path='./basin/overlay.png',
        shp_path='./shp/World_Countries_Generalized.shp',
        output_path='./tif_output/Basin_Malawi.tif'
    )
    
    visualizer.load_tif()
    visualizer.load_png()
    visualizer.load_shp()
    visualizer.process_and_save_tif()
