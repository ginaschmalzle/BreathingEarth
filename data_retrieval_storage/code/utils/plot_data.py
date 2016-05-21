import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.ticker import FuncFormatter
from mpl_toolkits.basemap import Basemap
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
import problem_sites


def make_xlabel(site, coordinate_dict):
    lat = round(coordinate_dict[site]['lat'], 3)
    lon = (360 - round(coordinate_dict[site]['lng'], 3)) * -1
    label ='{0}, Lat = {1} N, Lon = {2} W'.format(site, lat, lon)
    return label

def plot_single_site_ts(df, site, coordinate_dict, fig_size=(14,6), show = True):
    site_df = df.loc[ df['site'] == site ]
    fig, ax = plt.subplots(figsize=fig_size)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, pos: '%.0f'%x))
    ax.scatter(site_df['Dec_time'], site_df['adj_du'] * 1000., marker = 'o', label='rolling_median')
    ax.plot([2008,2016],[0,0], color = 'red')
    plt.xlim(2008, 2016)
    plt.xlabel(make_xlabel(site, coordinate_dict))
    plt.ylabel('Vertical Position (mm)')
    if show == True:
        plt.show()

def plot_subplot_ts(df, site, coordinate_dict, ax, fig_size=(14,6)):
    site_df = df.loc[ (df['site'] == site) & (df['Dec_time'] >= 2008.0)]
    ax.set_title(make_xlabel(site, coordinate_dict))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, pos: '%.0f'%x))
    ax.scatter(site_df['Dec_time'], site_df['adj_du'] * 1000., marker = 'o', label='rolling_median')
    ax.plot([2008,2016],[0,0], color = 'red')
    plt.ylabel('Vertical Position (mm)')

def plot_subset_of_site_ts(df, subset_sites, rows, columns, coordinate_dict, show = False, filename = None):
    '''Subset should contain 4 or less sites.'''
    f, plots = plt.subplots(rows, columns, sharex=True, sharey=True)
    plt.xlim(2008.0, 2016.0)
    plt.ylim(-50.0, 50.0)
    fig_size = (25,10)
    i = 0
    for row in plots:
        for item in row:
            try:
                pl = item
                site = subset_sites[i]
                i = i + 1
                plot_subplot_ts(df, site, coordinate_dict, pl, fig_size = fig_size)
            except:
                pass
    plt.savefig(filename)
    if show == True:
        plt.show()

def get_site_lol(sites, n_sites_per_page):
    site_lol = []; i = 1; site_temp = []
    for site in sites:
        if i > n_sites_per_page:
            i = 1
            site_lol.append(site_temp)
            site_temp = []
            site_temp.append(site)
        else:
            site_temp.append(site)
            i = i + 1
    site_lol.append(site_temp)
    return site_lol

def plot_all_site_ts(df, coordinate_dict, rows, columns, n):
    sites = df['site'].unique()
    filename = 'figures/time_series_' + str(n) + '.png'
    plot_subset_of_site_ts(df,
                           sites,
                           rows,
                           columns,
                           coordinate_dict,
                           show = False,
                           filename = filename)
    plt.close()

def plot_sites_on_map(coordinate_dict, problem_sites):
    m = Basemap(projection='merc',llcrnrlat=40,urcrnrlat=50,\
            llcrnrlon=-129,urcrnrlon=-118,resolution='i')
    # Draw the coastlines
    m.drawcoastlines()
    # Color the continents
    # Bug in drawcoastlines does not allow points mapped above land. We use drawlsmask instead.
    m.drawlsmask(land_color='0.8', ocean_color='w')
    # draw parallels and meridians.
    m.drawparallels(np.arange(-90.,91.,2.), labels=[1,0,0,0], fontsize=10)
    m.drawmeridians(np.arange(-180.,181.,2.), labels=[0,0,0,1], fontsize=10)
    plt.title("GPS sites")
    # Transform long and lat to the map projection
    # Each lat and long value in the maps above are 'mapped' to specific pixels that make up the image
    # The mapping, defined by the projection used, needs to also be done on the data set.
    lon = []; lat = []; prob_lon = []; prob_lat = []
    for key in coordinate_dict.keys():
        mod_lon = (360. - float(coordinate_dict[key]['lng'])) * -1.
        mod_lat = coordinate_dict[key]['lat']
        lon.append(mod_lon)
        lat.append(mod_lat)
        if key in problem_sites:
            prob_lon.append(mod_lon)
            prob_lat.append(mod_lat)
    x,y = m(lon, lat)
    px, py = m(prob_lon, prob_lat)
    # Now you can use the plt.scatter method to plot your data!
    plt.scatter(x, y, s = 20)
    plt.scatter(px, py, s = 20, color = 'red')
    filename = 'figures/gps_map.png'
    plt.savefig(filename)
    plt.show()


def get_table_data(medians, myrange, start_time):
    logging.info('starting to write to df')
    columns = ['time', 'pos', 'site', 'datetime', 'Dec_time', 'du']
    all_df = pd.DataFrame(columns = columns)
    retries = 0
    i = 0; b = False
    while i in range(0, myrange):
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
            b = True
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
            df['datetime'] = pd.to_datetime(df['time'], format='%Y-%m-%d %H:%M:%S')
            times = []
            for t in df['datetime']:
                times.append(utils.toYearFraction(t))
            df['Dec_time'] = times
            if len(df.loc[df.Dec_time == float(start_time)]) != 0:
                my_pos = []
                for item in df['pos']:
                    my_pos.append(float(item))
                df['du'] = my_pos
                zero_du = df.loc[(df.Dec_time == start_date)]['du'].unique()
                df['adj_du'] = df['du'] - zero_du
                all_df = all_df.append(df)
                i = i + 1
    return all_df, medians, b

def run():
    mpl.rcParams['figure.figsize'] = [30,20]
    mpl.rcParams.update({'font.size': 16})
    mpl.rcParams['figure.titlesize'] = 'medium'
    conn = utils.get_dynamo_conn(environment = 'local')
    median_table = Table('median_positions', connection = conn)
    medians_pnw = median_table.query_2(region__eq='pnw')
    medians_other = median_table.query_2(region__eq='other')
    rows = 4; columns = 4
    start_date = 2008.0
    n = 0; b == False
    for medians in [medians_other]:
        while b == False:
            df, medians, b = get_table_data(medians, rows * columns, start_date)
            sites = df['site'].unique()
            coordinate_dict = utils.get_dict_of_coordinates(conn, sites)
            plot_all_site_ts(df, coordinate_dict, rows, columns, n)
            n = n + 1
