import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
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
import sys
sys.path.insert(0, '../utils/utils.py')
import utils

conn = utils.get_dynamo_conn(environment = 'local')
df = utils.get_medians_df(conn)
sites = df['site'].unique()
coordinate_dict = utils.get_dict_of_coordinates(conn, sites)




def plot_single_site(df, site, coordinate_dict):
    site_df = df.loc[ df['site'] == site ]
    lat = round(coordinate_dict[site]['lat'], 3)
    lon = (360 - round(coordinate_dict[site]['lng'], 3)) * -1
    fig, ax = plt.subplots(figsize=(14,6))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, pos: '%.0f'%x))
    ax.scatter(site_df['Dec_time'], site_df['du'] * 1000., marker = 'o', label='rolling_median')
    ax.plot([2008,2016],[0,0], color = 'red')
    plt.xlim(2008, 2016)
    label ='{0}, Lat = {1} N, Lon = {2} W'.format(site, lat, lon)
    plt.xlabel(label)
    plt.ylabel('Vertical Position (mm)')
    plt.show()
