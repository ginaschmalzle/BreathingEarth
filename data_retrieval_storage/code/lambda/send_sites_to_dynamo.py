from get_data import my_handler
import os
import pandas as pd
import concurrent.futures
import glob

def download_pos_files():
    os.system('wget ftp://data-out.unavco.org/pub/products/position/pbo.nam08.pos.tar.gz')
    os.system('tar -zxvf pbo.nam08.pos.tar.gz')
    os.system('rm *.csv')

def read_csv_contents(pos_filename):
    ''' Read contents of csv and format for a dataframe.  Also collect site coordinates.'''
    site = pos_filename[:4]
    with open(pos_filename, 'r') as f:
        lines = []
        for row in f:
            splitrows = row.split()
            lines.append(splitrows)
        coordinate_data = { 'site' : site,
                            'lat' :decimal.Decimal(lines[8][4]),
                            'lon' :decimal.Decimal(lines[8][5])}
    return lines[35:], coordinate_data

def get_sites():
    ''' Define dataframe.  Also modify some columns to the correct data type. '''
    # all_sites = [x[:4] for x in glob.glob('*.pos')]
    # sites = []
    # for site in all_sites:
    #     filename = '{0}.pbo.nam08.pos'.format(site)
    #     lines, coordinate_data = read_csv_contents(filename)
    #     lat = coordinate_data['lat']; lon = coordinate_data['lon']
    #     if lon >= 232. and lon <= 242.:
    #         if lat >= 42. and lat <= 50.:
    #             sites.append(site)
    # unique_sites = list(set(sites))
    filename = 'ftpsource_sites.dat'
    with open(filename, 'r') as f:
        sites = []
        for row in f:
            if row[16:20] != '..",':
                sites.append(row[16:20])
    unique_sites = list(set(sites))
    return unique_sites

def run(async = True, environment = 'local'):
    # download_pos_files()
    sites = get_sites()
    context = {}
    if environment == 'local':
        if async == True:
            with concurrent.futures.ThreadPoolExecutor(max_workers = 5) as executor:
                for site in sites:
                    event = { 'site' : site,
                              'problem_site' : False }
                    futures = executor.submit(my_handler, event, context)
                # print ([future.result() for future in concurrent.futures.as_completed(futures)])
        else:
            for site in sites:
                event = { 'site' : site,
                          'problem_site' : False }
                message = my_handler(event, context)
                print message
