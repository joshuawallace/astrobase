#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''oldhatlc.py - Waqas Bhatti (wbhatti@astro.princeton.edu) - Jan 2014

Contains functions to read HAT LCs generated by the older HAT LC server. These
are presently in use for the http://hatnet.org and http://hatsouth.org light
curves of confirmed transiting planets found by HATNet and HATSouth
respectively. At some point in the future, these will be reissued as new format
light curves (readable by hatlc.py).

There is only one function in this module:

read_hatlc(hatlc) --> Read a retrieved HAT LC into a dict

See http://hatsouth.org/planets/lightcurves.html#lightcurve-schema for the light
curve format description.

'''
# put this in here because oldhatlc can be used as a standalone module
__version__ = '0.3.17'

import os.path
import gzip
import bz2

import numpy as np

HAVEPYFITS = False
try:

    import pyfits
    HAVEPYFITS = True

except Exception as e:
    from astropy.io import fits as pyfits
    HAVEPYFITS = True

finally:
    if not HAVEPYFITS:
        print("no pyfits module found (try pip install pyfits?). "
              "won't be able to read FITS format HAT LCs")
        HAVEPYFITS = False

#########################
## SETTINGS AND CONFIG ##
#########################

TEXTLC_OUTPUT_COLUMNS = {
    'BJD':['time in Baryocentric Julian Date',
           '%20.7f','D',float],
    'MJD':['time in Modified Julian Date',
           '%20.7f','D',float],
    'HJD':['time in Heliocentric Julian Date',
           '%20.7f','D',float],
    'RJD':['time in Reduced Julian Date',
           '%20.7f','D',float],
    'FJD':['time in Full Julian Date',
           '%20.7f','D',float],
    'XCC':['x coordinate on CCD',
           '%.1f','E',float],
    'YCC':['y coordinate on CCD',
           '%.1f','E',float],
    'IM1':['instrumental lightcurve magnitude (aperture 1)',
           '%12.5f','D',float],
    'IE1':['instrumental lightcurve measurement error (aperture 1)',
           '%12.5f','D',float],
    'IQ1':['instrumental lightcurve quality flag (aperture 1)',
           '%s','1A',str],
    'IM2':['instrumental lightcurve magnitude (aperture 2)',
           '%12.5f','D',float],
    'IE2':['instrumental lightcurve measurement error (aperture 2)',
           '%12.5f','D',float],
    'IQ2':['instrumental lightcurve quality flag (aperture 2)',
           '%s','1A',str],
    'IM3':['instrumental lightcurve magnitude (aperture 3)',
           '%12.5f','D',float],
    'IE3':['instrumental lightcurve measurement error (aperture 3)',
           '%12.5f','D',float],
    'IQ3':['instrumental lightcurve quality flag (aperture 3)',
           '%s','1A',str],
    'RM1':['reduced lightcurve magnitude (aperture 1)',
           '%12.5f','D',float],
    'RM2':['reduced lightcurve magnitude (aperture 2)',
           '%12.5f','D',float],
    'RM3':['reduced lightcurve magnitude (aperture 3)',
           '%12.5f','D',float],
    'EP1':['EPD lightcurve magnitude (aperture 1)',
           '%12.5f','D',float],
    'EP2':['EPD lightcurve magnitude (aperture 2)',
           '%12.5f','D',float],
    'EP3':['EPD lightcurve magnitude (aperture 3)',
           '%12.5f','D',float],
    'TF1':['TFA lightcurve magnitude (aperture 1)',
           '%12.5f','D',float],
    'TF2':['TFA lightcurve magnitude (aperture 2)',
           '%12.5f','D',float],
    'TF3':['TFA lightcurve magnitude (aperture 3)',
           '%12.5f','D',float],
    'RSTF':['HAT station and frame number of this LC point',
            '%s','10A',str],
    'RSTFC':['HAT station, frame number, and CCD of this LC point',
             '%s','10A',str],
    'ESTF':['HAT station and frame number of this LC point',
            '%s','10A',str],
    'ESTFC':['HAT station, frame number, and CCD of this LC point',
             '%s','10A',str],
    'TSTF':['HAT station and frame number of this LC point',
            '%s','10A',str],
    'TSTFC':['HAT station, frame number, and CCD of this LC point',
             '%s','10A',str],
    'FSV':['PSF fit S value',
           '%12.5f','E',float],
    'FDV':['PSF fit D value',
           '%12.5f','E',float],
    'FKV':['PSF fit K value',
           '%12.5f','E',float],
    'FLT':['filter used for this LC point',
           '%s','1A',str],
    'FLD':['observed HAT field',
           '%s','15A',str],
    'CCD':['CCD taking this LC point ',
           '%s','I',int],
    'CFN':['CCD frame number',
           '%s','I',int],
    'STF':['HAT station taking this LC point',
           '%s','I',int],
    'BGV':['Background value',
           '%12.5f','E',float],
    'BGE':['Background error',
           '%12.5f','E',float],
    'IHA':['Hour angle of object [hr]',
           '%12.5f','E',float],
    'IZD':['Zenith distance of object [deg]',
           '%12.5f','E',float],
    'NET':['HAT network responsible for this LC point',
           '%s','2A',str],
    'EXP':['exposure time for this LC point [seconds]',
           '%12.3f','E',float],
    'CAM':['camera taking the exposure for this LC point',
           '%s','2A',str],
    'TEL':['telescope taking the exposure for this LC point',
           '%s','2A',str],
    'XIC':['image-subtraction X coordinate on CCD',
           '%.1f','E',float],
    'YIC':['image-subtraction Y coordinate on CCD',
           '%.1f','E',float],
    'IRM1':['image-subtraction lightcurve reduced magnitude (aperture 1)',
           '%12.5f','D',float],
    'IRE1':['image-subtraction lightcurve measurement error (aperture 1)',
           '%12.5f','D',float],
    'IRQ1':['image-subtraction lightcurve quality flag (aperture 1)',
           '%s','1A',str],
    'IRM2':['image-subtraction lightcurve reduced magnitude (aperture 2)',
           '%12.5f','D',float],
    'IRE2':['image-subtraction lightcurve measurement error (aperture 2)',
           '%12.5f','D',float],
    'IRQ2':['image-subtraction lightcurve quality flag (aperture 2)',
           '%s','1A',str],
    'IRM3':['image-subtraction lightcurve reduced magnitude (aperture 3)',
           '%12.5f','D',float],
    'IRE3':['image-subtraction lightcurve measurement error (aperture 3)',
           '%12.5f','D',float],
    'IRQ3':['image-subtraction lightcurve quality flag (aperture 3)',
           '%s','1A',str],
    'IEP1':['image-subtraction EPD lightcurve magnitude (aperture 1)',
           '%12.5f','D',float],
    'IEP2':['image-subtraction EPD lightcurve magnitude (aperture 2)',
           '%12.5f','D',float],
    'IEP3':['image-subtraction EPD lightcurve magnitude (aperture 3)',
           '%12.5f','D',float],
    'ITF1':['image-subtraction TFA lightcurve magnitude (aperture 1)',
           '%12.5f','D',float],
    'ITF2':['image-subtraction TFA lightcurve magnitude (aperture 2)',
           '%12.5f','D',float],
    'ITF3':['image-subtraction TFA lightcurve magnitude (aperture 3)',
           '%12.5f','D',float],
    }




##############################
## READING RETRIEVED HATLCS ##
##############################

def read_hatlc(hatlc):
    '''
    This reads a consolidated HAT LC written by the functions above.

    Returns a dict.

    '''

    lcfname = os.path.basename(hatlc)

    # unzip the files first
    if '.gz' in lcfname:
        lcf = gzip.open(hatlc,'rb')
    elif '.bz2' in lcfname:
        lcf = bz2.BZ2File(hatlc, 'rb')
    else:
        lcf = open(hatlc,'rb')

    if '.fits' in lcfname and HAVEPYFITS:

        hdulist = pyfits.open(lcf)
        objectinfo = hdulist[0].header
        objectlc = hdulist[1].data
        lccols = objectlc.columns.names
        hdulist.close()
        lcf.close()

        lcdict = {}

        for col in lccols:
            lcdict[col] = np.array(objectlc[col])

        lcdict['hatid'] = objectinfo['hatid']
        lcdict['twomassid'] = objectinfo['2massid']
        lcdict['ra'] = objectinfo['ra']
        lcdict['dec'] = objectinfo['dec']
        lcdict['mags'] = [objectinfo[x] for x in ('vmag','rmag','imag',
                                                  'jmag','hmag','kmag')]
        lcdict['ndet'] = objectinfo['ndet']
        lcdict['hatstations'] = objectinfo['hats']
        lcdict['filters'] = objectinfo['filters']
        lcdict['columns'] = lccols

        return lcdict

    elif '.fits' in lcfname and not HAVEPYFITS:

        print("can't read %s since we don't have the pyfits module" % lcfname)
        return

    elif '.csv' in lcfname or '.hatlc' in lcfname:

        lcflines = lcf.read().decode().split('\n') # argh Python 3
        lcf.close()

        # now process the read-in LC
        objectdata = [x for x in lcflines if x.startswith('#')]
        objectlc = [x for x in lcflines if not x.startswith('#')]
        objectlc = [x for x in objectlc if len(x) > 1]

        if '.csv' in lcfname:
            objectlc = [x.split(',') for x in objectlc]
        else:
            objectlc = [x.split() for x in objectlc]

        # transpose split rows to get columns
        objectlc = list(zip(*objectlc)) # argh Python 3

        # read the header to figure out the object's info and column names
        objectdata = [x.strip('#') for x in objectdata]
        objectdata = [x.strip() for x in objectdata]
        objectdata = [x for x in objectdata if len(x) > 0]

        hatid, twomassid = objectdata[0].split(' - ')
        ra, dec = objectdata[1].split(', ')
        ra = float(ra.split(' = ')[-1].strip(' deg'))
        dec = float(dec.split(' = ')[-1].strip(' deg'))

        vmag, rmag, imag, jmag, hmag, kmag = objectdata[2].split(', ')
        vmag = float(vmag.split(' = ')[-1])
        rmag = float(rmag.split(' = ')[-1])
        imag = float(imag.split(' = ')[-1])
        jmag = float(jmag.split(' = ')[-1])
        hmag = float(hmag.split(' = ')[-1])
        kmag = float(kmag.split(' = ')[-1])

        ndet = int(objectdata[3].split(': ')[-1])
        hatstations = objectdata[4].split(': ')[-1]

        filterhead_ind = objectdata.index('Filters used:')
        columnhead_ind = objectdata.index('Columns:')

        filters = objectdata[filterhead_ind:columnhead_ind]

        columndefs = objectdata[columnhead_ind+1:]

        columns = []
        for line in columndefs:

            colnum, colname, coldesc = line.split(' - ')
            columns.append(colname)

        lcdict = {}

        # now write all the columns to the output dictionary
        for ind, col in enumerate(columns):

            # this formats everything nicely using our existing column
            # definitions
            lcdict[col] = np.array([TEXTLC_OUTPUT_COLUMNS[col][3](x)
                                    for x in objectlc[ind]])

        # write the object metadata to the output dictionary
        lcdict['hatid'] = hatid
        lcdict['twomassid'] = twomassid.strip('2MASS J')
        lcdict['ra'] = ra
        lcdict['dec'] = dec
        lcdict['mags'] = [vmag, rmag, imag, jmag, hmag, kmag]
        lcdict['ndet'] = ndet
        lcdict['hatstations'] = hatstations.split(', ')
        lcdict['filters'] = filters[1:]
        lcdict['cols'] = columns

        return lcdict
