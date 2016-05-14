from get_data import my_handler
import os
import pandas as pd
import concurrent.futures
import glob
import logging

logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter(
        '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

def get_sites():
    '''Return a list of unique sites in the UNAVCO FTP site.
    The file ftpsource_sites.dat is part of the website's
    'View Source' page.'''
    filename = 'ftpsource_sites.dat'
    with open(filename, 'r') as f:
        sites = []
        for row in f:
            if row[16:20] != '..",':
                sites.append(row[16:20])
    unique_sites = list(set(sites))
    return unique_sites

def run(async = True, environment = 'local'):
    '''Get the sites, and call get_data to load them.
    If environment == local, the script assumes get_data.py is in
    the working directory.  Otherwise, it assumes that it is a
    lambda function (not yet implemented).

    LAMBDA FUNCTION PROBLEM:  COULD NOT GET PANDAS AND NUMPY TO LOAD.

    ALSO NOTE -- ASYNC HAS A PROBLEM -- NOT ALL SITES LOADED.  I THINK
    THE PROBLEM CAN BE RESOLVED WITH AS_COMPLETED BUT STILL NEED TO TEST.'''

    sites = get_sites()
    # sites = [x[:4] for x in glob.glob('*.pos')]
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
                try:
                    event = { 'site' : site,
                              'problem_site' : False }
                    message = my_handler(event, context)
                    logging.info(message)
                except IOError as e:
                    logging.info(e)
    elif enivronment == 'lambda':
        pass
    else:
        pass
