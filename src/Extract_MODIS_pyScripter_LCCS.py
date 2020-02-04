# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Extract_NDVI.py
# Created on: 2019-12-04 09:21:32.00000
#   (generated by ArcGIS/ModelBuilder)
# Description:
# ---------------------------------------------------------------------------

# Import arcpy module
import arcpy
import numpy as np
import os
import glob
import sys
from datetime import datetime

arcpy.env.overwriteOutput = True
arcpy.CheckOutExtension('Spatial')

# data required: MODIS product, tiles and dates
var, layer = 'PFT', '4'
product = 'MCD12Q1'
#factor = 0.1
tiles = ['h17v04']
dateslim = None

# paths
pathMODIS = 'F:/Codigo/GitHub/MODIS/'
pathData = 'F:/OneDrive - Universidad de Cantabria/Cartografia/MODIS/' + product + '/'
pathOutput = 'F:/Cartografia/MODIS/' + product + '/'
if os.path.exists(pathOutput) == False:
    os.makedirs(pathOutput)
#pathTemp = 'C:/Users/casadoj/Documents/ArcGIS/Default.gdb/'
pathTemp = 'F:/Cartografia/MODIS/temp/'
if os.path.exists(pathTemp):
    #Cleanup
    arcpy.Delete_management(pathTemp)
os.makedirs(pathTemp)


# DEM
mdt = pathMODIS + 'data/dem.asc'

# Input and output coordinate system
coordsMODIS = 'PROJCS["Sinusoidal",GEOGCS["GCS_Undefined",DATUM["D_Undefined",SPHEROID["User_Defined_Spheroid",6371007.181,0.0]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.017453292519943295]],PROJECTION["Sinusoidal"],PARAMETER["False_Easting",0.0],PARAMETER["False_Northing",0.0],PARAMETER["Central_Meridian",0.0],UNIT["Meter",1.0]]'
coordsOut = 'PROJCS["ETRS89/UTM zone 30N",GEOGCS["ETRS89",DATUM["D_ETRS_1989",SPHEROID["GRS_1980",6378137,298.257222101]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]],PROJECTION["Transverse_Mercator"],PARAMETER["latitude_of_origin",0],PARAMETER["central_meridian",-3],PARAMETER["scale_factor",0.9996],PARAMETER["false_easting",500000],PARAMETER["false_northing",0],UNIT["Meter",1]]'

# convert date limits to datetime
if dateslim is not None:
    # convertir fechas límite en datetime.date
    start = datetime.strptime(dateslim[0], '%Y-%m-%d').date()
    end = datetime.strptime(dateslim[1], '%Y-%m-%d').date()

# select dates and files
dates, files = {tile: [] for tile in tiles}, {tile: [] for tile in tiles}
for tile in tiles:
    # seleccionar archivos del producto para las hojas y fechas indicadas
    for file in [f for f in os.listdir(pathData) if (product in f) & (tile in f)]:
        year = file.split('.')[1][1:5]
        doy = file.split('.')[1][5:]
        date = datetime.strptime(' '.join([year, doy]), '%Y %j').date()
        if dateslim is not None:
            if (date >= start) & (date <= end):
                dates[tile].append(date)
                files[tile].append(file)
        else:
            dates[tile].append(date)
            files[tile].append(file)
# create a joined, unique array of dates
dates = np.sort(np.unique(np.array([date for tile in tiles for date in dates[tile]])))

# extract and manage data
for d, date in enumerate(dates):
    dateStr = str(date.year) + str(date.timetuple().tm_yday).zfill(3)
    print(dateStr)

    # outFile
    outFile = product.lower() + '_a' + dateStr + '.asc'
    print(outFile)
    if os.path.exists(pathOutput + outFile):
        continue

    hdfs = {}
    for t, tile in enumerate(tiles):

        # file of the prescribed date and tile
        file = [f for f in files[tile] if dateStr in f][0]

        # extract file
        hdfs[tile] = arcpy.ExtractSubDataset_management(pathData + file, pathTemp + 'tile' + str(t), layer)

        # Process: Raster Calculator
        #hdfs[tile] = arcpy.gp.RasterCalculator_sa(hdfs[tile] * factor, factored_hdf)

        # Process: Define Projection
        #arcpy.DefineProjection_management(hdfs[tile], coordsMODIS)

    # Process: Mosaic To New Raster
    if len(tiles) > 1:
        inputs = ''
        for t in range(len(tiles)):
            inputs += pathTemp + 'tile' + str(t)
            if t < len(tiles) -1:
                inputs += ';'
        mosaic = pathTemp + "mosaic"
        arcpy.MosaicToNewRaster_management(inputs, pathTemp, "mosaic", "", "16_BIT_SIGNED", "", "1", "LAST", "FIRST")
    else:
        mosaic = pathTemp + 'tile0'

    # Process: Project Raster
    rasterPrj = pathTemp + "rasterPrj"
    arcpy.ProjectRaster_management(mosaic, rasterPrj, coordsOut, "NEAREST", "463.3127165275 463.3127165275", "", "", "")

    # Process: Extract by Mask
    rasterExt = pathTemp + "rasterExt"
    arcpy.gp.ExtractByMask_sa(rasterPrj, mdt, rasterExt)

    # Process: Raster to ASCII (2)
    outFile = pathOutput + file[:16].replace('.', '_') + '_' + var + '.asc'
    arcpy.RasterToASCII_conversion(rasterExt, outFile)

    #for f in os.listdir(pathTemp):
    #    os.remove(f)

arcpy.Delete_management(pathTemp)

