# -*- coding: utf-8 -*-
"""
Created on Thu Mar 26 07:41:30 2015
Last Update: 11 May 2017

@author: jessica scheick
Script modified from (downloaded 26 Mar 2015):
    #Steve Kochaver
    #kochaver.python@gmail.com
    #Version Date 2014-7-14


DESCRIPTION: calculate top of atmosphere reflectance (including the solar correction)
for Landsat imagery. For Landsat <7, this requires also calculating radiance.

SYNTAX:
python full_path_to_script/Landsat_TOARefl.py [full path of metadata file ending in '/', metadata filename, "SITType", true/false, bands]
    files will be saved in metadata_file_path (so in imagery folder) with same naming convention as original band file names + "_refl"
    true/false indicates whether or not to keep the intermediary radiance files
    see getESUN function for SITTypes (which vary by Landsat and aren't needed for LS8); I've been using 'ETM+ Thuillier'
"""

import sys, os, math, time
from osgeo import gdal
import raster as raster

##########  Functions  ##########    
def acquireMetadata(metadata, band):
    band = str(band)
    metadatalist = []
    SPACECRAFT_ID = "SPACECRAFT_ID"

    #data needed for Landsats 4,5, and 7
    if metadata["SPACECRAFT_ID"] == "LANDSAT_7":
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
    
    #data needed for Landsat 8 Reflectance only (need to add more if also want to calc radiance)        
    elif metadata["SPACECRAFT_ID"] == "LANDSAT_8":
        BANDFILE = "FILE_NAME_BAND_" + band
        REFLECTANCE_MULT = "REFLECTANCE_MULT_BAND_" + band 
        REFLECTANCE_ADD = "REFLECTANCE_ADD_BAND_" + band 
        DATE = "DATE_ACQUIRED"
        metadatalist = [SPACECRAFT_ID, BANDFILE, REFLECTANCE_MULT, REFLECTANCE_ADD, DATE]

    else:
        print 'There was a problem reading the metadata for this file. Please make sure the _MTL.txt is in Level 1 data format'
        
    return metadatalist


#Calculate the radiance from metadata on band. For Landsats 7 and earlier
def calcRadiance (LMAX, LMIN, QCALMAX, QCALMIN, path, QCAL, band):
    
    LMAX = float(LMAX)
    LMIN = float(LMIN)
    QCALMAX = float(QCALMAX)
    QCALMIN = float(QCALMIN)
    offset = (LMAX - LMIN)/(QCALMAX-QCALMIN)
    inraster_open = gdal.Open(path+QCAL)
    inraster_array = inraster_open.GetRasterBand(1).ReadAsArray() 
    radiance = path + 'RadianceB'+str(band)+'.tif'
#    radiance = path+path[-22:-1]+'_B'+str(band)+'_radiance.tif'
    inraster_open = None

    '''
    print 'Band'+str(band)
    print 'LMAX = '+str(LMAX)
    print 'LMIN = '+str(LMIN)
    print 'QCALMAX = '+str(QCALMAX)
    print 'QCALMIN = '+str(QCALMIN)
    print 'offset = '+str(offset)
    '''    
    
    outraster_array = (offset * (inraster_array-QCALMIN)) + LMIN
    radiance = raster.rasterfile(path+QCAL, radiance, outraster_array, dtype=gdal.GDT_Float32)
    
    return radiance


#calculate reflectance from radiance and other values; for Landsat7 and earlier
def calcReflectance(solarDist, ESUN, solarElevation, radianceRaster, path, scaleFactor):
    
#    print 'entering reflectance fn'
    #Value for solar zenith is 90 degrees minus solar elevation (angle from horizon to the center of the sun)
    #http://landsathandbook.gsfc.nasa.gov/data_properties/prog_sect6_3.html
    #note: I'm not sure why the orig. author converts to solarZenith (an extra step) - you 
    #can also keep solarElevation and use sin in the calculation    
    solarZenith = ((90.0 - (float(solarElevation)))*math.pi)/180 #Converted from deg to rad (python takes angles in rad)
    solarDist = float(solarDist)
    ESUN = float(ESUN)
#    print radianceRaster
    radiance_open = gdal.Open(radianceRaster)
    radiance_array = radiance_open.GetRasterBand(1).ReadAsArray() 
#    reflectance = path + 'ReflecB'+str(band)+'.tif'
    reflectance = path+path[-22:-1]+'_B'+str(band)+'_refl.tif'
    radiance_open = None
    
#     print 'Band'+str(band)
#     print 'solarDist = '+str(solarDist)
#     #print 'solarDistSquared ='+str(math.pow(solarDist, 2))
#     print 'ESUN = '+str(ESUN)
#     print 'solarZenith = '+str(solarZenith)
    outraster_array = (math.pi * radiance_array * math.pow(solarDist, 2)) / (ESUN * math.cos(solarZenith)) * scaleFactor
    reflectance = raster.rasterfile(radianceRaster, reflectance, outraster_array, dtype=gdal.GDT_Float32)
    return reflectance
    
    
def LS8_calcReflectance(refl_mult, refl_add, solarElevation, path, QCAL):
    
#    print 'LS8_calcReflectance entered' #
    solarElevationRad = (float(solarElevation)*math.pi)/180 #Converted from degr to rad (python takes angles in rad)
    refl_mult = float(refl_mult)
    refl_add = float(refl_add)
    inraster_open = gdal.Open(path+QCAL)
    inraster_array = inraster_open.GetRasterBand(1).ReadAsArray() 
    reflectance = path+path[-22:-1]+'_B'+str(band)+'_refl.tif'
    inraster_open = None
    
    # print 'Band'+str(band)
#     print 'solarElevation (radians) = '+str(solarElevationRad)
#     print 'refl_mult = ' + str(refl_mult)
#     print 'refl_add = ' + str(refl_add)

    outraster_array = ((refl_mult * inraster_array) + refl_add) / (math.sin(solarElevationRad))
    reflectance = raster.rasterfile(path+QCAL, reflectance, outraster_array, dtype=gdal.GDT_Float32)
    
    return reflectance


#Calculate the solar distance based on day of year (doy)   
def calcSolarDist (doy):

    #Values taken from d.csv file which is a formatted version of the d.xls file
    #associated with the Landsat7 handbook, representing the distance of the sun
    #for each day of year (1-366).
    #landsathandbook.gsfc.nasa.gov/excel_docs/d.xls (included in the parent folder)
    #this line keeps the relative path were this script is executing
    filepath = os.path.join(os.path.dirname(sys.argv[0]), 'd.csv')
    
    f = open(filepath, "r")
    lines = f.readlines()[1:]
    
    distances = []
    for x in range(len(lines)):
        distances.append(float(lines[x].strip().split(',')[1]))
    f.close()
    doy = int(doy)
    dist = distances[doy - 1]
    
    return dist 

def calcDOY (date):
    
    #Seperate date aspects into list (check for consistnecy in formatting of all
    #Landsat7 metatdata) YYYY-MM-DD
    dt = date.rsplit("-")

    #Cast each part of the date as a in integer in the 9 int tuple mktime
    t = time.mktime((int(dt[0]), int(dt[1]), int(dt[2]), 0, 0, 0, 0, 0, 0))

    #As part of the time package the 7th int in mktime is calulated as day of year
    #from the completion of other essential parts of the tuple
    doy = time.gmtime(t)[7]

    return doy


def getESUN(bandNum, SIType):
    SIType = SIType
    ESUN = {}
    #from NASA's Landsat7 User Handbook Table 11.3 http://landsathandbook.gsfc.nasa.gov/pdfs/Landsat7_Handbook.pdf
    #ETM+ Solar Spectral Irradiances(generated using the Thuillier solar spectrum)
    #for "relatively clear Landsat scenes"
    if SIType == 'ETM+ Thuillier':
        ESUN = {'b1':1997,'b2':1812,'b3':1533,'b4':1039,'b5':230.8,'b7':84.90,'b8':1362}

    #from NASA's Landsat7 User Handbook Table 11.3 http://landsathandbook.gsfc.nasa.gov/data_prod/prog_sect11_3.html
    #ETM+ Solar Spectral Irradiances (generated using the combined Chance-Kurucz Solar Spectrum within MODTRAN 5)
    if SIType == 'ETM+ ChKur':
        ESUN = {'b1':1970,'b2':1842,'b3':1547,'b4':1044,'b5':225.7,'b7':82.06,'b8':1369}

    #from NASA's Landsat7 User Handbook Table 9.1 http://landsathandbook.gsfc.nasa.gov/pdfs/Landsat7_Handbook.pdf
    #from the LPS ACCA algorith to correct for cloud cover
    #mean solar spectral irradiances prior to ACCA (???)
    if SIType == 'LPS ACAA Algorithm':
        ESUN = {'b1':1969,'b2':1840,'b3':1551,'b4':1044,'b5':225.7,'b7':82.07,'b8':1368}
        #note: changed b7 value from orig. 82.06 to 82.07, as listed in table 9.1 (31 Mar 2015)

    #from Revised Landsat-5 TM Radiometric Calibration Procedures and Postcalibration
    #Dynamic Ranges Gyanesh Chander and Brian Markham. Nov 2003. Table II. http://landsathandbook.gsfc.nasa.gov/pdfs/L5TMLUTIEEE2003.pdf
    #Landsat 4 ChKur
    if SIType == 'Landsat 5 ChKur':
        ESUN = {'b1':1957,'b2':1825,'b3':1557,'b4':1033,'b5':214.9,'b7':80.72}
    
    #from Revised Landsat-5 TM Radiometric Calibration Procedures and Postcalibration
    #Dynamic Ranges Gyanesh Chander and Brian Markham. Nov 2003. Table II. http://landsathandbook.gsfc.nasa.gov/pdfs/L5TMLUTIEEE2003.pdf
    #Landsat 4 ChKur
    if SIType == 'Landsat 4 ChKur':
        ESUN = {'b1':1957,'b2':1826,'b3':1554,'b4':1036,'b5':215,'b7':80.67} 

    bandNum = str(bandNum)
    
    return ESUN[bandNum]


def readMetadata(metadataFile):
    f = metadataFile
    
    #Create an empty dictionary with which to populate all the metadata fields.
    metadata = {}

    #Each item in the txt document is seperated by a space and each key is
    #equated with '='. This loop strips and seperates then fills the dictonary.

    for line in f:
        if not line.strip() == "END":
            val = line.strip().split('=')
            metadata [val[0].strip()] = val[1].strip().strip('"')      
        else:
            break
	
    return metadata


#Takes the unicode parameter input from Arc and turns it into a nice python list
def cleanList(bandList):
    
    bandList = list(bandList)
    
    for x in range(len(bandList)):
        bandList[x] = str(bandList[x])
        
    while ';' in bandList:
        bandList.remove(';')
        
    return bandList


#////////////////////////////////////MAIN LOOP///////////////////////////////////////
if __name__ == "__main__":
    #Parameters from input
        #input format is python full-script-path [relative path of metadata file, "SITType", true/false, bands]
        #note sys.argv[0] is automatically the path to the dir where the script is executed
        #here, you must be within the imagery folder for the script to run
        #true/false indicates whether or not to keep the intermediary radiance files
    ##print 'cwd is ', os.getcwd()
    ##os.path.dirname(os.path.abspath(sys.argv[0]))
    ##print 'cwd is now ', os.getcwd()
    metadataPath = sys.argv[1]
    metadataName = sys.argv[2]
    SIType = str(sys.argv[3])
    keepRad = str(sys.argv[4])
    scaleFactor = 1 ##float(sys.argv[4]) #scalefactor is not in the handbook as part of the calculation, but for simplicity I'm keeping the variable...
    #bandList must be entered as a list of band numbers with no seperators (e.g. 125, not 1;2;5 nor 1,2,5)
    bandList = cleanList(sys.argv[5]) #must change this to sys.argv[5] if scaleFactor is included as an input
    #print 'bandList is: ', bandList
    
    metadataFile = open(metadataPath+metadataName)
    metadata = readMetadata(metadataFile)
    metadataFile.close()
    
    successful = []
    failed = []
    
    for band in bandList:
        band = str(band)
        metlist = acquireMetadata(metadata, band)
        SPACECRAFT_ID = metlist[0] 
        
        #Landsat 4,5,7 radiance and reflectance calculation
        if metadata["SPACECRAFT_ID"] == 'LANDSAT_7':
            BANDFILE = metlist[1]
            LMAX = metlist[2]
            LMIN = metlist[3]
            QCALMAX = metlist[4]
            QCALMIN = metlist[5]
            DATE = metlist[6]
            ESUNVAL = "b" + band
            
            #print 'bandfile is ', metadata[BANDFILE] #
            try:
                radianceRaster = calcRadiance(metadata[LMAX], metadata[LMIN], metadata[QCALMAX], metadata[QCALMIN], metadataPath, metadata[BANDFILE], band)
                #print 'radianceRaster successfully executed'    

                doy = calcDOY(metadata[DATE])
                #print 'doy is ', doy    #
                        
                reflectanceRaster = calcReflectance(calcSolarDist(calcDOY(metadata[DATE])), getESUN(ESUNVAL, SIType), metadata['SUN_ELEVATION'], radianceRaster, metadataPath, scaleFactor)
                #print 'reflectanceRaster successfully executed'
                
                #simply deletes the unneeded radianceRaster
                if keepRad != 'true':
                    cmd = 'rm -f ' + radianceRaster
                    os.system(cmd)
    
                successful.append(BANDFILE)
    
            except Exception, e:
                failed.append(band)
                failed.append(str(e))
                
        #Landsat 8 reflectance calculation (only)
        elif metadata["SPACECRAFT_ID"] == 'LANDSAT_8':
            BANDFILE = metlist[1]
            REFLECTANCE_MULT = metlist[2]
            REFLECTANCE_ADD = metlist[3]
            DATE = metlist[4]
        
            #print 'bandfile is ', metadata[BANDFILE] #
            
            try:
                reflectanceRaster = LS8_calcReflectance(metadata[REFLECTANCE_MULT], metadata[REFLECTANCE_ADD], metadata['SUN_ELEVATION'], metadataPath, metadata[BANDFILE])
                #print 'reflectanceRaster successfully executed' #
    
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