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
        self.malawi_boundary = None

    def load_tif(self):
        self.tif_data = rasterio.open(self.tif_path)
    def load_png(self):
        self.overlay_png_data = Image.open(self.overlay_png_path).convert('L')

    def load_shp(self):
        self.shp_data = gpd.read_file(self.shp_path)

        self.malawi_boundary = self.shp_data[self.shp_data['COUNTRY'] == 'Malawi']
        if self.malawi_boundary.empty:
            raise ValueError()

    def process_and_save_tif(self):
        if self.tif_data is None or self.shp_data is None or self.overlay_png_data is None:
            raise ValueError()

        bbox = gpd.GeoDataFrame({'geometry': [box(32, -18, 36, -9)]}, crs=self.shp_data.crs)

        out_image, out_transform = mask(self.tif_data, bbox.geometry, crop=True)
        out_meta = self.tif_data.meta.copy()
        out_meta.update({"driver": "GTiff",
                         "height": out_image.shape[1],
                         "width": out_image.shape[2],
                         "transform": out_transform})

        malawi_image, malawi_transform = mask(self.tif_data, self.malawi_boundary.geometry, crop=True)
        malawi_image[malawi_image == self.tif_data.nodata] = 0

        overlay_array = np.array(self.overlay_png_data)
        overlay_resized = np.array(Image.fromarray(overlay_array).resize((malawi_image.shape[2], malawi_image.shape[1]), Image.NEAREST))

        if overlay_resized.shape != malawi_image.shape[1:]:
            raise ValueError()

        overlay_masked, _ = mask(self.tif_data, self.malawi_boundary.geometry, crop=True, filled=True, nodata=0)
        overlay_resized[overlay_masked[0] == 0] = 0

        combined_image = malawi_image.copy()
        combined_image[:, overlay_resized == 255] = 255

        malawi_meta = self.tif_data.meta.copy()
        malawi_meta.update({
            "driver": "GTiff",
            "height": combined_image.shape[1],
            "width": combined_image.shape[2],
            "transform": malawi_transform
        })

        output_dir = os.path.dirname(self.output_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        with rasterio.open(self.output_path, "w", **malawi_meta) as dest:
            dest.write(combined_image)

if __name__ == "__main__":
    visualizer = ArcGIS_Overlapper(
        tif_path='./tif/Basin_FlowDi2.tif',
        overlay_png_path='./basin/overlay.png',
        shp_path='./shp/World_Countries_Generalized.shp',
        output_path='./tif_output/Basin_FlowDi2_Malawi.tif'
    )
    
    visualizer.load_tif()
    visualizer.load_png()
    visualizer.load_shp()
    visualizer.process_and_save_tif()
