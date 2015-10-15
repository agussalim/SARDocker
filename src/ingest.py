#!/usr/bin/env python
#******************************************************************************
#  Name:  ingest.py
#  Purpose:
#    utility to ingest georeferenced single, dual or quad polSAR 
#    files generated by polSARpro/MapReady 
#    from TerraSAR-X, Radarsat-2, Cosmo-Skymed SLC images and 
#    convert to a single 9-band (quad), 4-band (dual), or 1-band (single), 
#    float32 image.
#
#   Usage:
#   import ingest
#   ingets.ingest(path)
#        or
#   python ingest.py [-h] indir
#
#  Copyright (c) 2015, Mort Canty
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

import os, re, sys, getopt, time
import numpy as np
from osgeo import gdal
from osgeo.gdalconst import GA_ReadOnly, GDT_Float32

def ingest(path):    
    print '========================='
    print '     Ingest SAR'
    print '========================='
    print time.asctime()  
    print 'Directory %s'%path 
    
    start = time.time()
    try:
    #  get sorted list of covariance matrix element files    
        files1 = os.listdir(path)
        files = []
        for afile in files1:
            if re.search('C[1-3]{2}',afile):   # covarinace matrix format
                files.append(afile)
            elif re.search('T[1-3]{2}',afile): # coherency matix format
                files.append(afile)
        files.sort()        
        bands = len(files)
    #  get real and imaginary in right order    
        if bands==9:
            tmp = files[1]
            files[1] = files[2]
            files[2] = tmp
            tmp = files[3]
            files[3] = files[4]
            files[4] = tmp
            tmp = files[6]
            files[6] = files[7]
            files[7] = tmp
        elif bands == 4:
            tmp = files[1]
            files[1] = files[2]
            files[2] = tmp
    #  get image dimensions
        outfn = 'polSAR.tif'
        gdal.AllRegister()   
        inDataset = gdal.Open(files[0],GA_ReadOnly)
        cols = inDataset.RasterXSize
        rows = inDataset.RasterYSize       
    #  create the output file
        driver = gdal.GetDriverByName('GTiff') 
        outDataset = driver.Create(outfn,cols,rows,bands,GDT_Float32)
        projection = inDataset.GetProjection()
        geotransform = inDataset.GetGeoTransform()
        if geotransform is not None:
            outDataset.SetGeoTransform(geotransform)
        if projection is not None:
            outDataset.SetProjection(projection)
        inDataset = None     
    #  ingest
        for i in range(bands):
            print 'writing band %i'%(i+1)
            inDataset = gdal.Open(files[i])
            inBand = inDataset.GetRasterBand(1)
            band = inBand.ReadAsArray(0,0,cols,rows).astype(np.float32)
            outBand = outDataset.GetRasterBand(i+1)
            outBand.WriteArray(band)
            outBand.FlushCache()
            inDataset = None
        outDataset = None
        print 'elapsed time: ' + str(time.time() - start)
        return outfn
    except Exception as e:
        print 'Error %s  --Image could not be read in'%e 
        return None     
     
    
def main():
    usage = '''
Usage:
------------------------------------------------
python %s [-h] indir

Enter directory containing the geo-referenced and terrain-corrected
polarimetric covariance matrix elements (as generated by MapReady).
------------------------------------------------''' %sys.argv[0]

    options, args = getopt.getopt(sys.argv[1:],'h')  
    for option, _ in options:
        if option == '-h':
            print usage
            return        
    if len(args) != 1:
        print 'Incorrect number of arguments'
        print usage
        sys.exit(1)  
    os.chdir(args[0])
    if os.path.isfile('polSAR.tif'):
        print 'Overwriting previous combined image'
    outfn = ingest(args[0])
    if outfn is not None:
        print 'Multiband image is %s'%(args[0]+outfn)
    
if __name__ == '__main__':
    main()
    