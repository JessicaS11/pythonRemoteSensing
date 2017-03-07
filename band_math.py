# -*- coding: utf-8 -*-
"""
Last update: 9 June 2015

@author: Jessica Scheick

DESCRIPTION:
functions to compute Landsat band math, many of which include a masking prior
to calculations and/or a thresholding post calculations

functions:
    NDSI (using green and SWIR/NIR 1.55-1.75micron)
    two band average

NOTES:
Pay attention to data type (in and out) to avoid "wrong" math and odd results

"""

#import sys, os, math
from osgeo import gdal
import numpy as np

#def array_thresh (inarray,threshold)


#classifies the image using the NDSI and a given threshold, then writes to a raster file
    #sets a no-data value of -99
def classify_NDSI (bandi, bandj, outfile, threshold):
    #declare variables
    NODATA = -99
    inTYPE = np.float32
    outTYPE = gdal.GDT_Float32
    
    #open input files, read in arrays, and convert to signed int for calculation    
    bandi_open = gdal.Open(bandi)
    bandi_array = bandi_open.GetRasterBand(1).ReadAsArray()
    bandi_array = bandi_array.astype(inTYPE, copy=False)
    bandj_open = gdal.Open(bandj)
    bandj_array = bandj_open.GetRasterBand(1).ReadAsArray()
    bandj_array = bandj_array.astype(inTYPE, copy=False)
    
    #compute NDSI ((i-j)/(i+j)), including zero handling for division
    band_diff = bandi_array - bandj_array    
    band_sum = bandi_array + bandj_array
    is_zero = (band_sum==0)
    band_sum[is_zero] = 1
    class_array = band_diff / band_sum
    class_array[is_zero] = NODATA 
    
#    print 'bandi val ' + str(bandi_array[3475,6137]) + ' bandj val ' + str(bandj_array[3475,6137])
#    print 'band_diff val ' + str(band_diff[3475,6137]) + ' band_sum val ' + str(band_sum[3475,6137])
#    print 'NDSI: ' + str(class_array[3475,6137])
    
    #threshold image
#    outfile_array = class_array
    outfile_array = class_array > threshold

    
    #get geo info from original (uses bandi file/info)
    geo = bandi_open.GetGeoTransform()
    #create new GeoTiff, apply georef info, and write new raster
    outfile_open = gdal.GetDriverByName('GTiff').Create(outfile, bandi_array.shape[1], bandi_array.shape[0], 1, outTYPE)
    outfile_open.SetGeoTransform((geo[0], geo[1], geo[2], geo[3], geo[4], geo[5]))
    outfile_open.SetProjection(bandi_open.GetProjection())
    outfile_open.GetRasterBand(1).WriteArray(outfile_array)
    outfile_open.GetRasterBand(1).SetNoDataValue(NODATA)
    
   
    outfile_open = None
    bandi_open = None
    bandj_open = None
    print 'NDSI complete'    
    
    return outfile
  
  
#given two input band filenames and a mask file to ignore values (!=1),
    #calculates the average of the two bands and 
    #thresholds the image to keep everything above the specified threshold
def classify_twob_avg (bandi, bandj, mask, outfile, threshold):
    #declare variables
    NODATA = -99
    inTYPE = np.float32
    outTYPE = gdal.GDT_Float32
    
    #open input files, read in arrays, and convert to signed int for calculation        
    bandi_open = gdal.Open(bandi)
    bandi_array = bandi_open.GetRasterBand(1).ReadAsArray()
    bandi_array = bandi_array.astype(inTYPE, copy=False)
    bandj_open = gdal.Open(bandj)
    bandj_array = bandj_open.GetRasterBand(1).ReadAsArray()
    bandj_array = bandj_array.astype(inTYPE, copy=False)
    
    mask_open = gdal.Open(mask)
    mask_array = mask_open.GetRasterBand(1).ReadAsArray()
    ignore = (mask_array!=1)
    
    #compute average
    band_avg = (bandi_array + bandj_array) / 2
    band_avg[ignore] = NODATA
    
    #threshold image
    outfile_array = band_avg > threshold

    #get geo info from original (uses bandi file/info)
    geo = bandi_open.GetGeoTransform()
    #create new GeoTiff, apply georef info, and write new raster
    outfile_open = gdal.GetDriverByName('GTiff').Create(outfile, bandi_array.shape[1], bandi_array.shape[0], 1, outTYPE)
    outfile_open.SetGeoTransform((geo[0], geo[1], geo[2], geo[3], geo[4], geo[5]))
    outfile_open.SetProjection(bandi_open.GetProjection())
    outfile_open.GetRasterBand(1).WriteArray(outfile_array)
    outfile_open.GetRasterBand(1).SetNoDataValue(NODATA)    
   
    outfile_open = None
    bandi_open = None
    bandj_open = None
    mask_open = None
    print 'band avg complete'    
    
    return outfile   

   