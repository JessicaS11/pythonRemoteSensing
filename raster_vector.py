# -*- coding: utf-8 -*-
"""
Last update: 3 Sept. 2015

@author: Jessica Scheick

DESCRIPTION:
Perform raster-vector file operations, including conversions between the two

FUNCTIONS:
    creates a raster mask with extent of raster file input given a polygon shapefile;
        an attribute value can be specified to provide the raster [burn] value (CreateRasterMask)

NOTES:

"""
import os
from osgeo import gdal, ogr

# Creates raster mask fitting the input dataset (ds) using the polygon shapefile vector_fn
# The rasterized mask is named raster_fn
#note that an output raster file is generated, but the function itself returns the mask array
def CreateRasterMask(ds, raster_fn, vector_fn, burn_val = ''):
    # Open vector file and get Layer
    vec_ds = ogr.Open(vector_fn)
    vec_layer = vec_ds.GetLayer()

    # Get GeoTransform of Geotiff to be masked
    geo = ds.GetGeoTransform()

    # Create the mask geotiff
    print "check for correct output type (e.g. UInt16) for raster pixel values"
#####    mask_ds = gdal.GetDriverByName('GTiff').Create(raster_fn, ds.RasterXSize, ds.RasterYSize, 1, gdal.GDT_Byte)
    mask_array = gdal.GetDriverByName('GTiff').Create(raster_fn, ds.RasterXSize, ds.RasterYSize, 1, gdal.GDT_UInt16)
    mask_array.SetGeoTransform((geo[0], geo[1], geo[2], geo[3], geo[4], geo[5]))
    mask_array.SetProjection(ds.GetProjection())
    band = mask_array.GetRasterBand(1)
    band.SetNoDataValue(-999)

    # Rasterize (vector file is rasterized into the projection of the original dataset, ds)
    #can also add options for including pixels that are partially within the polygon, rather than the default of only entire pixels
    if not burn_val:
        gdal.RasterizeLayer(mask_array, [1], vec_layer, burn_values=[1])
    else:
        gdal.RasterizeLayer(mask_array, [1], vec_layer, options = ["ATTRIBUTE="+burn_val])

    vec_ds = None
    return mask_array