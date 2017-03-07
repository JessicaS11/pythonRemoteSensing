# -*- coding: utf-8 -*-
"""
Created on Thu Jul  2 14:34:57 2015

@author: jessica

DESCRIPTION:
Gets the necessary info and does the requied calculations (including calculating radiance)
required to calculate the brightness temperature (in K) of a Landsat thermal band

FUNCTIONS:
    acquireMetadata (specifically to get the vars needed to compute brightness temps)
    LS8_calcRadiance
    calcBrightTemp

SYNTAX:
    python full-script-path/BrightTempCalc.py [relative path of metadata file, true/false, band]
    here, you must be within the imagery folder for the script to run
    true/false indicates whether or not to keep the intermediary radiance files\
    
Notes:
!!Currently does low gain (VCID-1) for Landsat 7; must be adjusted for high gain (in acquireMetadata) or for other Landsats (4,5)
!!You can only do one band at a time (due to LS8 bands being 10 and 11, ie double digit)
"""

import raster
import sys, os
import gdal
import numpy as np

sys.path.append('/Users/jessica/Scripts/imganal_python/TOAReflecCalc/')
import Landsat_TOARefl as toa

##########  Functions  ##########    
#NOTE: this function is very similar to the version in Landsat_TOARefl, only it grabs slightly different info for doing brightness temp calcs (esp for LS8)
def acquireMetadata(metadata, band):
    band = str(band)
    metadatalist = []
    SPACECRAFT_ID = "SPACECRAFT_ID"

    #data needed for Landsats 4,5, and 7 radiance
    if metadata["SPACECRAFT_ID"] == "LANDSAT_7":
        #determine band 6 gain setting for LS7        
        band = band + "_VCID_1"
        print "NOTICE: Using LOW GAIN thermal band for Landsat 7"
        #Metadata exists in one of two standard formats (finds the correct name for each field)
        if ("RADIANCE_MAXIMUM_BAND_" + band) in metadata.keys(): 
            BANDFILE = "FILE_NAME_BAND_" + band
            LMAX = "RADIANCE_MAXIMUM_BAND_" + band
            LMIN = "RADIANCE_MINIMUM_BAND_" + band
            QCALMAX = "QUANTIZE_CAL_MAX_BAND_" + band
            QCALMIN = "QUANTIZE_CAL_MIN_BAND_" + band
            DATE = "DATE_ACQUIRED"
            metadatalist = [SPACECRAFT_ID, BANDFILE, LMAX, LMIN, QCALMAX, QCALMIN, DATE]
    
        elif ("LMAX_BAND" + band) in metadata.keys():
            BANDFILE = "BAND" + band + "_FILE_NAME"
            LMAX = "LMAX_BAND" + band
            LMIN = "LMIN_BAND" + band
            QCALMAX = "QCALMAX_BAND" + band
            QCALMIN = "QCALMIN_BAND" + band
            DATE ="ACQUISITION_DATE"
            metadatalist = [SPACECRAFT_ID, BANDFILE, LMAX, LMIN, QCALMAX, QCALMIN, DATE]
    
    #data needed for Landsat 8 radiance and thermal brightness      
    elif metadata["SPACECRAFT_ID"] == "LANDSAT_8":
        BANDFILE = "FILE_NAME_BAND_" + band
        RADIANCE_MULT = "RADIANCE_MULT_BAND_" + band 
        RADIANCE_ADD = "RADIANCE_ADD_BAND_" + band 
        K1 = "K1_CONSTANT_BAND_" + band
        K2 = "K2_CONSTANT_BAND_" + band
        DATE = "DATE_ACQUIRED"
        metadatalist = [SPACECRAFT_ID, BANDFILE, RADIANCE_MULT, RADIANCE_ADD, K1, K2, DATE]

    else:
        print 'There was a problem reading the metadata for this file. Please make sure the _MTL.txt is in Level 1 data format'
        
    return metadatalist


#calculatethe radiance from metadata on band. For landsat 8
def LS8_calcRadiance (rad_mult, rad_add, QCAL, band):

    rad_mult = float(rad_mult)
    rad_add = float(rad_add)
    inraster_open = gdal.Open(QCAL)
    inraster_array = inraster_open.GetRasterBand(1).ReadAsArray() 
    radiance = 'RadianceB'+str(band)+'.tif'
    inraster_open = None
    
    outraster_array = ((rad_mult * inraster_array) + rad_add)
    radiance = raster.rasterfile(QCAL, radiance, outraster_array, dtype=gdal.GDT_Float32)
    
    return radiance


#calculates brightness temperature for LS5,7,8, in Kelvin
def calcBrightTemp (K1, K2, radiance, band):

    K1 = float(K1)
    K2 = float(K2)
    inraster_open = gdal.Open(radiance)
    inraster_array = inraster_open.GetRasterBand(1).ReadAsArray() 
    BT = 'BrightnessTempB'+str(band)+'.tif'
    inraster_open = None
    
    if not inraster_array.all():
        print 'inraster_array empty'
        sys.exit
    
    is_zero = (inraster_array<=0)
    inraster_array[is_zero] = 1   
    
    outraster_array = (K2 / (np.log((K1/inraster_array) + 1)))
    outraster_array[is_zero] = 0
    BrightTemp = raster.rasterfile(radiance, BT, outraster_array, dtype=gdal.GDT_Float32)
    
    return BrightTemp
    

#////////////////////////////////////MAIN LOOP///////////////////////////////////////
#Parameters from input
    #input format is python full-script-path [relative path of metadata file, true/false, band]
    #here, you must be within the imagery folder for the script to run

metadataPath = sys.argv[1]
keepRad = str(sys.argv[2])
band = str(sys.argv[3])

metadataFile = open(metadataPath)
metadata = toa.readMetadata(metadataFile)
metadataFile.close()

successful = []
failed = []


#NOTE: although some fn are simply called from Landsat_TOARefl, acquireMetadata is modified herein to get the needed variables
metlist = acquireMetadata(metadata, band)
SPACECRAFT_ID = metlist[0] 

#Landsat 7 thermal band brightness temperature calculation
if metadata["SPACECRAFT_ID"] == 'LANDSAT_7':
    BANDFILE = metlist[1]
    LMAX = metlist[2]
    LMIN = metlist[3]
    QCALMAX = metlist[4]
    QCALMIN = metlist[5]
    DATE = metlist[6]
    
    #set thermal band calibration constants for LS7 (different for LS5!!!)
    #from LS7 Handbook: http://landsathandbook.gsfc.nasa.gov/data_prod/prog_sect11_3.html
    K1 = 666.09  #watts/(meter squared*ster*micron)
    K2 = 1282.71  #Kelvin
    
    print 'bandfile is ', metadata[BANDFILE] #
    try:
        radianceRaster = toa.calcRadiance(metadata[LMAX], metadata[LMIN], metadata[QCALMAX], metadata[QCALMIN], metadata[BANDFILE], band)
        print 'radianceRaster successfully executed'    
                
        brightnessRaster = calcBrightTemp (K1, K2, radianceRaster, band)
        print 'brightnessRaster successfully executed'

        #simply deletes the unneeded radianceRaster
        if keepRad != 'true':
            cmd = 'rm -rf ' + radianceRaster
            os.system(cmd)

        successful.append(BANDFILE)

    except Exception, e:
        failed.append(band)
        failed.append(str(e))
        
#Landsat 8 radiance and then brightness temp calculation
elif metadata["SPACECRAFT_ID"] == 'LANDSAT_8':
    BANDFILE = metlist[1]
    RADIANCE_MULT = metlist[2]
    RADIANCE_ADD = metlist[3]
    K1 = metlist[4]
    K2 = metlist[5]
    DATE = metlist[6]

    print 'bandfile is ', metadata[BANDFILE] #
    
    try:
        radianceRaster = LS8_calcRadiance (metadata[RADIANCE_MULT], metadata[RADIANCE_ADD], metadata[BANDFILE], band)
        print 'radianceRaster successfully executed' #
        
        brightnessRaster = calcBrightTemp (metadata[K1], metadata[K2], radianceRaster, band)
        print 'brightness temperature successfully executed'

        #simply deletes the unneeded radianceRaster
        if keepRad != 'true':
            cmd = 'rm -rf ' + radianceRaster
            os.system(cmd)
            
        successful.append(BANDFILE)

    except Exception, e:
        failed.append(band)
        failed.append(str(e))                        

if successful:
   print "The following files were converted successfully:"
   for x in successful:
        print metadata[x]

if failed:
    for x in range(0,len(failed),2):
        print "Band" + str(failed[x]) + " failed to execute. Error: " + failed[x+1]
        if "object is not callable" in failed[x+1]:
            print 'This error catching is not 100%, it probably worked anyway'