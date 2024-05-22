import rasterio
import geopandas as gpd
import matplotlib.pyplot as plt
from rasterio.plot import show
from rasterio.mask import mask
from shapely.geometry import box

class BasinOverlayer:
    def __init__(self, tif_path: str, shp_path: str):
        self.tif_path = tif_path
        self.shp_path = shp_path
        self.tif_data = None
        self.shp_data = None

    def load_tif(self):
        self.tif_data = rasterio.open(self.tif_path)

    def load_shp(self):
        self.shp_data = gpd.read_file(self.shp_path)

    def plot_tif_on_shp(self):
        if self.tif_data is None or self.shp_data is None:
            raise ValueError()

        bbox = gpd.GeoDataFrame({'geometry': [box(32, -18, 36, -9)]}, crs=self.shp_data.crs)

        out_image, out_transform = mask(self.tif_data, bbox.geometry, crop=True)
        out_meta = self.tif_data.meta.copy()
        out_meta.update({"driver": "GTiff",
                         "height": out_image.shape[1],
                         "width": out_image.shape[2],
                         "transform": out_transform})

        fig, ax = plt.subplots(figsize=(10, 10))
        self.shp_data.plot(ax=ax, color='none', edgecolor='blue')
        show(out_image, transform=out_transform, ax=ax)
        plt.show()

if __name__ == "__main__":
    Visualizer = BasinOverlayer(tif_path='./tif_output/Basin_FlowDi2_Malawi.tif', shp_path='./shp/World_Countries_Generalized.shp')
    Visualizer.load_tif()
    Visualizer.load_shp()
    Visualizer.plot_tif_on_shp()
