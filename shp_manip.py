# -*- coding: utf-8 -*-
"""
Last update: 9 March 2015

@author: jessica scheick

DESCRIPTION:
shapefile manipulations, including a series of functions to aid in preparation
of shapefiles for entry into the GLIMS database

functions:
    add requisite fields to GLIMS shapefile
    remove inner rings from polygons
    

NOTES:

"""

import sys, os, math
from osgeo import gdal, ogr, osr

#creates/modifies a shapefile to have the requisite GLIMS fields
def GLIMS_shapefile (outfile):
    driver = ogr.GetDriverByName('ESRI Shapefile')
    
    #create shapefile and add fields    
    '''
    ds = driver.CreateDataSource( outfile + ".shp" )
    layer = ds.CreateLayer(outfile, srs = None )
    '''    
    #use already existing shapfile and add fields    
    ds = driver.Open( outfile + '.shp', 1 )
    layer = ds.GetLayer()
    
    #defines attribute fields needed and their properties
    field_name = ['line_type','anlys_id','glac_id','anlys_time',\
    'area','db_area','width','length','min_elev','mean_elev','max_elev',\
    'src_date','rec_status','glac_name','wgms_id','local_id','glac_stat',\
    'subm_id','release_dt','proc_desc','rc_ic','geog_area','chief_affl',\
    'submitters','analysts']
    
    field_type = ['string','real','string','string',\
    'real','real','real','real','real','real','real',\
    'string','string','string','string','string','string',\
    'real','string','string','real','string','string',\
    'string','string']
    
    field_length = [20,20,20,20,20,20,20,20,20,20,20,20,20,20,20,20,\
    20,20,20,20,254,20,25,25,80,80]
    
    field_precision = [0,0,0,0,6,6,6,6,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    
    #adds the fields to the shapefile    
    for i in range(0, len(field_name)):
        if field_type[i] == 'string':
            f_type = ogr.OFTString
        elif field_type[i] == 'real':
            f_type = ogr.OFTReal
        
        fldDef = ogr.FieldDefn(field_name[i], f_type)
        fldDef.SetWidth(field_length[i])
        fldDef.SetPrecision(field_precision[i])
        
        #adds attribute fields to layer
        layer.CreateField(fldDef)
        
    return outfile


#takes a preexisting polygon shapefile and checks each polygon for inner rings
#   removes inner rings from polygons that have them and writes to a new file
def remove_innerrings(inshpfile, outshpfile):
    driver = ogr.GetDriverByName('ESRI Shapefile')
    #open shapefile and grab spatial reference info
    ds = driver.Open(inshpfile, 0)
    inLayer = ds.GetLayer()
    srs = osr.SpatialReference()
    srs.ImportFromWkt( inLayer.GetSpatialRef().ExportToWkt() )
        
    # Remove output shapefile if it already exists
    if os.path.exists(outshpfile):
        driver.DeleteDataSource(outshpfile)

    # Create the output shapefile (srs = spatial reference)
    outDataSource = driver.CreateDataSource(outshpfile)
    out_lyr_name = os.path.splitext( os.path.split( outshpfile )[1] )[0]
    outLayer = outDataSource.CreateLayer( out_lyr_name, geom_type=ogr.wkbMultiPolygon, srs = srs)

    # Add input Layer Fields to the output Layer if it is the one we want
    inLayerDefn = inLayer.GetLayerDefn()
    #print 'inlayerdefn is ', inLayerDefn
    for i in range(0, inLayerDefn.GetFieldCount()):
        fieldDefn = inLayerDefn.GetFieldDefn(i)
        outLayer.CreateField(fieldDefn)

    # Get the output Layer's Feature Definition
    outLayerDefn = outLayer.GetLayerDefn()
    #print 'outlayerdefn is ', outLayerDefn

    # Add features to the ouput Layer
    for inFeature in inLayer:
        # Create output Feature
        outFeature = ogr.Feature(outLayerDefn)

        # Add field values from input Layer
        for i in range(0, outLayerDefn.GetFieldCount()):
            fieldDefn = outLayerDefn.GetFieldDefn(i)
            outFeature.SetField(outLayerDefn.GetFieldDefn(i).GetNameRef(),
                inFeature.GetField(i))

        # Set geometry
        geometry = inFeature.GetGeometryRef()
        geomWkt = geometry.ExportToWkt()
        newGeomWkt, trash = geomWkt.split(')', 1)
        newGeomWkt = newGeomWkt + '))'
        newGeom = ogr.CreateGeometryFromWkt(newGeomWkt)
        outFeature.SetGeometry(newGeom)
        outLayer.CreateFeature(outFeature)
        
        #alt: newGeom = geometry.GetGeometryRef(0)
        #extracts first sub-geometry (outerring) from polygon
        #avoids changing to/from wkt, but changes geom from polygon to connectedring (or something similar)

        #geometry = outFeature.GetGeometryRef()
        #print geometry
        
    # Close DataSources
    ds.Destroy()
    outDataSource.Destroy()
