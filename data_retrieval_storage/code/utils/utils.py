import matplotlib.pyplot as plt
import boto
import boto.dynamodb2
from boto.dynamodb2.table import Table
import os
import pandas as pd
from time import sleep
import logging
from datetime import datetime as dt
import numpy as np
import datetime
import time

logging.basicConfig(filename='HISTORYlistener.log',level=logging.INFO,
                    format='%(asctime)s.%(msecs)d %(levelname)s %(module)s - %(funcName)s: %(message)s',
                    datefmt="%Y-%m-%d %H:%M:%S")

def get_dynamo_conn(environment = 'local'):
    ''' Get connection to Dynamo DB.  AWS keys stored as environment variables if run locally.
    'environment' does not need to be stated if running on lambda.'''
    try:
        if event['environment'] == 'local':
            conn = boto.dynamodb2.connect_to_region('us-west-2',
                                                    aws_access_key_id = os.environ['AWSKEY'],
                                                    aws_secret_access_key = os.environ['AWSSECRET'])
    except:
            conn = boto.dynamodb2.connect_to_region('us-west-2')
    return conn

def toYearFraction(mydate):
    date = datetime.datetime.strptime(str(mydate), '%Y-%m-%d %H:%M:%S')
    def sinceEpoch(date): # returns seconds since epoch
        return time.mktime(date.timetuple())
    s = sinceEpoch

    year = date.year
    startOfThisYear = dt(year=year, month=1, day=1)
    startOfNextYear = dt(year=year+1, month=1, day=1)

    yearElapsed = s(date) - s(startOfThisYear)
    yearDuration = s(startOfNextYear) - s(startOfThisYear)
    fraction = yearElapsed/yearDuration

    return date.year + fraction

def get_dict_of_coordinates(conn, sites):
    ''' sites is a list of sites'''
    coordinate_table = Table('site_coordinates', connection = conn)
    coordinate_dict = {}
    for site in sites:
        try:
            item = coordinate_table.get_item(site = site)
        except:
            sleep(3)
            item = coordinate_table.get_item(site = site)
        stuff = {}
        for i in item.items():
            if i[0] == 'lat' or i[0] == 'lon':
                stuff.update({ i[0]: float(i[1]) })
            else:
                stuff.update({ i[0]:i[1] })
        coordinate_dict.update( { stuff['site']: { 'lat' : stuff['lat'],
                                                   'lng' : stuff['lon'] }})
    return coordinate_dict

def get_site_obs(conn, site):
    logging.info('Getting raw observations for site {0}'.format(site))
    obs_table = Table('vertical_positions', connection = conn)
    item = obs_table.get_item(site = site)
    return item.items()

def get_medians_df(conn):
    logging.info('Connecting to Median table')
    median_table = Table('median_positions', connection = conn)
    medians = median_table.query_2(region__eq='pnw')
    logging.info('Queried Medians in PNW')
    logging.info('starting to write to df')
    columns = ['time', 'pos', 'site']
    all_df = pd.DataFrame(columns = columns)
    retries = 0
    while True:
        try:
            item = medians.next()
            site = item['site']
            print 'Got site {0}'.format(site)
        except boto.dynamodb2.exceptions.ProvisionedThroughputExceededException:
            sleepTime = min(60, (2.**retries)/10.)
            logging.info('Sleeping for %.02f secs' % sleepTime)
            sleep(sleepTime)
            item = None
            retries += 1 if retries < 10 else 0
        except:
            break
        if item == None:
            continue
        else:
            site = item['site']; region = item['region']
            logging.info('Importing site {0}'.format(site))
            df = pd.DataFrame(item.items(), columns = ['time', 'pos'])
            df['site'] = pd.DataFrame(site, index=np.arange(len(df['time'])),columns=['site'])
            df = df[df.time != 'region']; df = df[df.time != 'site']; df = df[df.time != 'problem_site']
            logging.info(df.columns)
            all_df = all_df.append(df)
    all_df['datetime'] = pd.to_datetime(all_df['time'], format='%Y-%m-%d %H:%M:%S')
    times = []
    for t in all_df['datetime']:
        times.append(toYearFraction(t))
    all_df['Dec_time'] = times
    my_pos = []
    for item in all_df['pos']:
        my_pos.append(float(item))
    all_df['du'] = my_pos
    logging.info('Finished writing to dataframe.')
    return all_df
