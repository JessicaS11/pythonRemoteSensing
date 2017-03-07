# -*- coding: utf-8 -*-
"""
last update: April 2015

@author: Jessica Scheick

DESCRIPTION:
series of functions to filter (open and close) raster images using erosion and dilation
opening an image removes noise
closing an image connects lines/points that are disjointed
    erosion removes single pixels surrounded by a different value
    dilation enlarges large areas ("smooths" edges)


NOTES:
must manually edit filter window size
deals only with integer values (must edit if want to filter floats)
"""

from osgeo import gdal
import numpy as np
import cv2

##currently doesn't address boundaries (simply uses defaults)
##watch for filter window size and integer values (vs floats)
#applies an opening filter (erosion followed by dilation) to reduce noise
def openraster (infile):
    infile_open = gdal.Open(infile)
    infile_array = infile_open.GetRasterBand(1).ReadAsArray()  
    #averaging window    
    kernel = np.ones((3,3),np.uint8)
    
    #open image (erode, then dilate)
    outfile_array = cv2.morphologyEx(infile_array, cv2.MORPH_OPEN, kernel)
    
    #create new GeoTiff, apply georef info, and write new raster
    outfile = infile[:-4] + '_opened.tif'    
    geo = infile_open.GetGeoTransform()
    outfile_open = gdal.GetDriverByName('GTiff').Create(outfile, infile_array.shape[1], infile_array.shape[0], 1, gdal.GDT_Byte)
    outfile_open.SetGeoTransform((geo[0], geo[1], geo[2], geo[3], geo[4], geo[5]))
    outfile_open.SetProjection(infile_open.GetProjection())
    outfile_open.GetRasterBand(1).WriteArray(outfile_array)    
    
    infile_open = None
    outfile_open = None
    
    return outfile
    
    
##currently doesn't address boundaries (simply uses defaults)
##watch for filter window size and integer values (vs floats)
#applies a closing filter (dilation followed by erosion) to reduce noise
def closeraster (infile):
    infile_open = gdal.Open(infile)
    infile_array = infile_open.GetRasterBand(1).ReadAsArray()  
    #averaging window    
    kernel = np.ones((3,3),np.uint8)
    
    #close image (dilate, then erod)
    outfile_array = cv2.morphologyEx(infile_array, cv2.MORPH_CLOSE, kernel)
    
    #create new GeoTiff, apply georef info, and write new raster
    outfile = infile[:-4] + '_closed.tif'    
    geo = infile_open.GetGeoTransform()
    outfile_open = gdal.GetDriverByName('GTiff').Create(outfile, infile_array.shape[1], infile_array.shape[0], 1, gdal.GDT_Byte)
    outfile_open.SetGeoTransform((geo[0], geo[1], geo[2], geo[3], geo[4], geo[5]))
    outfile_open.SetProjection(infile_open.GetProjection())
    outfile_open.GetRasterBand(1).WriteArray(outfile_array)    
    
    infile_open = None
    outfile_open = None
    
    return outfile

