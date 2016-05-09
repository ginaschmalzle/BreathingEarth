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

def select_sites_that_have_data_on_date(df, start_date):
    ''' Returns a dataframe containing only sites that
    have data on start_date.  The value of the vertical
    position on that date is then used as a reference date
    and is subtracted from all other values for that site.
    Date in format 'YYYY-MM-DD' '''
    # Select sites
    # Only use values that start on or after start_date
    df = df.loc[(df.Dec_time >= start_date)]
    selected_sites = df.loc[(df.Dec_time == start_date)]
    selected_df = pd.DataFrame(columns = df.columns)
    for s in selected_sites.site.unique():
        # Get value of du at start date
        zero_du = df.loc[(df.Dec_time == start_date) & (df.site == s)]['du'].unique()
        # Only collect information on the site
        site_df = df.loc[df.site == s]
        # Create an adjusted du column, that subtracts the vertical position
        # on the first day
        site_df['adj_du'] = site_df['du'] - zero_du[0]
        selected_df = selected_df.append(site_df)
    return selected_df

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

def plot_subset_of_site_ts(df, subset_sites, rows, columns, coordinate_dict, show = True, filename = None):
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

def plot_all_site_ts(df, coordinate_dict):
    rows = 4; columns = 4
    sites = df['site'].unique()
    site_lol = get_site_lol(sites, rows * columns)
    i = 0
    for subset_sites in site_lol:
        filename = 'figures/time_series_' + str(i) + '.png'
        i = i + 1
        plot_subset_of_site_ts(df,
                               subset_sites,
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

def run():
    mpl.rcParams['figure.figsize'] = [30,20]
    mpl.rcParams.update({'font.size': 16})
    mpl.rcParams['figure.titlesize'] = 'medium'

    conn = utils.get_dynamo_conn(environment = 'local')
    df_all = utils.get_medians_df(conn)
    df = select_sites_that_have_data_on_date(df_all, 2008.0)

    sites = df['site'].unique()
    coordinate_dict = utils.get_dict_of_coordinates(conn, sites)
    plot_all_site_ts(df, coordinate_dict)
    problem_sites = ['COUP', 'P693', 'P703','P316','P664','CPUD',
                     'P694','P705','P430','P660','CSHR','P697','PUPU',
                     'P442','P665','ORS1','P699','P064', 'P655', 'P666',
                     'ORS2', 'P702','P158', 'P667','P668', 'P673']
