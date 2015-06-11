# -*- coding: utf-8 -*-
"""
Last update: 9 June 2015

@author: jessica scheick

DESCRIPTION:
this script generates a glacier outline using NDSI with a threshold value of 0.5
and band average with a threshold of 60
NDSI uses the green and SWIR/NIR (1.55-1.75 micron) bands ((gr-NIR)/(gr+NIR))
average uses green and NIR (0.76-0.90 micron) bands
    <=LS7: Green = B2, NIR = B4, NIR/SWIR = B5
 
The classification is exported to a shapefile with the requesite fields
(and inner rings removed) for ingestion into the GLIMS glacier database.
Manual corrections and population of the attribute table must be subsequently completed

NOTES:
The following must be changed within the body of the script/functions:
bands (if others are needed), threshold values, output shapefile name, ROI mask

REQUIREMENTS:
shapefile outlining region of interest (in same directory as script; name modified in code below)
directory containing a landsat rasters with required bands 

SYNTAX:
$ python ~/Scripts/imganal_python/GlacDelin/outline_glac.py ./LT50080672007238CUB00/LT50080672007238CUB00_B2.TIF 2007238
Run in the directory containing the script, using relative paths to the required
imagery. Arguments include one(any) band geotiff (script internally grabs needed bands)
and output file "root", usually YYYYDOY


"""

import sys, os
import band_math as bmath
import shp_manip as shp
import raster as raster

##########  Functions  ##########
#converts classified raster into polygon shapefile
def polygonize2shapefile (raster_infile, shape_outfile):        
    #using optimized python function
    #print 'shape_outfile is ', shape_outfile    
    cmd = 'gdal_polygonize.py ' + raster_infile + ' -b 1 -f "ESRI Shapefile" ' + shape_outfile
    os.system(cmd)    
     
    return shape_outfile

    #using polygonize function, which took forever/didn't finish
    '''  
    src_ds = gdal.Open(raster_infile)
    if src_ds is None:
        print 'Unable to open %s' % raster_infile
        sys.exit(1)
    
    try:
        srcband = src_ds.GetRasterBand(1)
    except RuntimeError, e:
        # for example, try GetRasterBand(10)
        print 'Band ( %i ) not found' % 1
        print e
        sys.exit(1)    

    driver = ogr.GetDriverByName('ESRI Shapefile')
    dst_ds = driver.Open( shape_outfile + '.shp', 1 )
    ##dst_layer = dst_ds.CreateLayer(outfile, srs = None )
    layer = dst_ds.GetLayer()
    gdal.Polygonize( srcband, None, layer, -1, [], callback=None )    
    src_ds = None
    dst_ds = None
    
    return shape_outfile
    '''

    
########  MAIN  ########
#variables (for threshold and ouput filnames)
NDSIthresh = 0.5
avgthres = 60

#inputs are any image file path (eg ./LT50080661997242XXX03/LT50080661997242XXX03_BX.TIF) and YYYYDOY for results
inputs = sys.argv[1]
name = inputs.split('/')[-1]
outroot = sys.argv[2]  #this is the only output that needs to be changed; the rest of the names will generate automatically

#determine Landsat era to construct needed band filenames
if int(name[2]) in [8]:
    bandgrfile = inputs[0:-5] + "3.TIF"
    bandNIR1file = inputs[0:-5] + "5.TIF"
    bandNIR2file = inputs[0:-5] + "6.TIF"
    pixelsz = 30
    print 'landsat 8'
    
elif int(name[2]) in [4,5,7]:
    bandgrfile = inputs[0:-5] + "2.TIF"
    bandNIR1file = inputs[0:-5] + "4.TIF"
    bandNIR2file = inputs[0:-5] + "5.TIF"
    pixelsz = 30
    print 'landsat 4,5,7'

else:
    print 'Not Landsat imagery'

#construct output filenames
outname1 = outroot + "_NDSI.tif"
outname2 = outroot + "_NDSIavg.tif"
outcut = outroot + "_NDSIavg_cut.tif"
intshapename = outroot + '_innerrings'
shapename = outroot + '_auto'
mask_raster = 'QQW.shp'

outname1 = bmath.classify_NDSI(bandgrfile, bandNIR2file, outname1, NDSIthresh)
outname2 = bmath.classify_twob_avg(bandgrfile, bandNIR1file, outname1, outname2, avgthres)
outcut = raster.trim_raster(outname2, mask_raster, outcut, pixelsz)
#print 'outcut is ', outcut
polygonize2shapefile(outcut,shapename)
shp.remove_innerrings('./'+ shapename+ '/out.shp', shapename)
shp.GLIMS_shapefile('./' + shapename + '/' + shapename)

'''
#rename shapefile and associated files in shapedir
for f in os.listdir('./' + shapename):
    d = './' + shapename + '/'
    suffix = f.split('.')[1]
    newf = shapename + '.' + suffix
    cmd = 'mv ' + d + f + ' ' + d + newf
    os.system(cmd) 
'''

