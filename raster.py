# -*- coding: utf-8 -*-
"""
Last update: 9 June 2015

@author: Jessica Scheick

DESCRIPTION:
Perform raster file operations, such as write out a new array to a georeferenced
rasterfile and trim a raster to a shapefile for faster processing

NOTES:
trim_raster fn assumes projections match --> ideally this step would include a check and alert/reprojection
"""
import os
from osgeo import gdal

#creates a georeferenced tif raster file with the same dimensions and geo info/proj coord sys as the parent raster
def rasterfile (infile, new_raster_name, new_raster_array, dtype):    
    #read in original raster (input file) as an array
    infile_open = gdal.Open(infile)
    infile_array = infile_open.GetRasterBand(1).ReadAsArray()  
    
    #get geo info from original
    geo = infile_open.GetGeoTransform()
    
    #create new GeoTiff, apply georef info, and write new raster
    outfile = gdal.GetDriverByName('GTiff').Create(new_raster_name, infile_array.shape[1], infile_array.shape[0], 1, dtype)
    outfile.SetGeoTransform((geo[0], geo[1], geo[2], geo[3], geo[4], geo[5]))
    outfile.SetProjection(infile_open.GetProjection())
    outfile.GetRasterBand(1).WriteArray(new_raster_array)
   
    infile_open = None
    outfile= None
    return new_raster_name
    
    
#trims a raster to a shapefile (along pixel boundaries) of the ROI [to reduce polygonizing computation time]
def trim_raster (infile, mask, outfile, pxsz):
    #optional code to get and print projection information (reprojection needs to be added to code)    
    '''
    ds = gdal.Open(infile)
    proj1 = ds.GetProjection()
    print proj1
    ds = None
    
    driver = ogr.GetDriverByName('ESRI Shapefile')
    ds = driver.Open(mask, 1)
    layer = ds.GetLayer()
    proj2 = layer.GetSpatialRef()
    print proj2
    ds = None
    '''
    print 'CHECK TO MAKE SURE PROJECTIONS MATCH'
    
###could use warp options of gdalwarp to include all touched pixels rather than just pixels with centers in the shapefile    
    #print "Cutting parent raster"
    cmd = "gdalwarp -tr " + str(pxsz) + " " + str(pxsz) + " -tap -cutline " + mask + " -crop_to_cutline " + infile + " " +  outfile
    os.system(cmd)
    
    #translate raster by half a pixel width (in m) so shapefile matches pixel edges rather than pixel centers    
    ds = gdal.Open(outfile, gdal.GA_Update)
    geo = ds.GetGeoTransform()
    #print 'geo0 ', geo[0], ' and geo3 ', geo[3]
    geo_0 = geo[0] + pxsz/2
    geo_3 = geo[3] - pxsz/2
    print "edit division here if pixels don't line up"
    new_geo = (geo_0, geo[1], geo[2], geo_3, geo[4], geo[5])
    ds.SetGeoTransform(new_geo)
    
    #geo = ds.GetGeoTransform()
    #print 'geo0 ', geo[0], ' and geo3 ', geo[3]
    ds = None
    
    return outfile
    
