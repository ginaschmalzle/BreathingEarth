import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.ticker import FuncFormatter
import sqlite3
import pandas as pd
import numpy as np
import datetime
import simplekml

db = '../populate_tables/breathingearth.db'
conn = sqlite3.connect(db)

def get_precip(conn):
    cursor = conn.cursor()
    sql = 'SELECT PST, PrecipitationIn FROM weather;'
    with conn:
        response = cursor.execute(sql)
    datatuples = response.fetchall()
    df = pd.DataFrame(datatuples, columns = ['date', 'precip_inches'])
    precipi = df.precip_inches;  precipi_list = precipi.tolist()
    for i in range(0, len(precipi_list)):
        if type(precipi_list[i]) == unicode:
            precipi_list[i] = 0.0
        else:
            precipi_list[i] = float(precipi_list[i]) * 2.54  # convert to cm
    date_list = df['date'].tolist()
    month_list = []
    for d in date_list:
        split_list = d.split('-')
        mo = '{0}-{1}'.format(split_list[0], split_list[1])
        month_list.append(mo)
    df['month'] = month_list
    df['precip_cm'] = precipi_list
    df['datetime'] = pd.to_datetime(df.date)
    return df

def get_monthly_sums(df):
    monthly_sums = df.groupby('month')['precip_cm'].sum()
    return monthly_sums

def coordinates_to_kml(conn):
    sql = 'SELECT * FROM coordinates;'
    with conn:
        response = conn.execute(sql)
    content = response.fetchall()
    kml = simplekml.Kml()
    for item in content:
        kml.newpoint(name = item[0],
                     description="Vertical GPS Position (mm)",
                     coords=[(item[2]-360, item[1])])
    kml.save('gps.kml')
    return content

def plot_sites_on_map(coordinate_dict):
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
    x,y = m(lon, lat)
    # Now you can use the plt.scatter method to plot your data!
    plt.scatter(x, y, s = 20)
    filename = 'figures/gps_map.png'
    plt.savefig(filename)
    plt.show()

def plot_weather_with_GPSsite(monthly_sums, site, site_df):
    mpl.rcParams.update({'font.size': 16})
    mpl.rcParams['figure.titlesize'] = 'medium'
    sums = monthly_sums.values.tolist()
    mo = monthly_sums.keys().tolist()
    dates = []
    for m in mo:
        dates.append(datetime.datetime.strptime(m, "%Y-%m").date())
    fig = plt.figure()
    fig.set_size_inches(15.,5., forward = True)
    ax = plt.subplot(111)
    # ax.yaxis.tick_right()
    # ax.yaxis.set_label_position("right")
    ax.set_ylabel('Precipitation, Monthly Sum (mm)', color = 'b')
    ax.set_xticks(np.arange(len(dates)), 1)
    ax.bar(dates, sums, 30, alpha=0.3)
    # ax.set_xlim([2008,2016.5])
    for tl in ax.get_yticklabels():
        tl.set_color('b')

    site_x = site_df['datetime'].tolist()
    site_y = site_df['Position_mm'].tolist()
    ax2 = ax.twinx()
    # ax2.set_xlim([2008,2016.5])
    # ax.yaxis.tick_left()
    # ax.yaxis.set_label_position("left")
    ax2.set_ylabel('SEAT Vertical Position (mm)', color = 'r')
    ax2.scatter(site_x, site_y, c='red', alpha = 0.3, lw = 0)
    for tl in ax2.get_yticklabels():
        tl.set_color('r')
    plt.savefig('SEAT_and_precip.png')
    plt.show()

def get_single_site(site, conn, min_date):
    sql = 'SELECT Date, Up from positions where site = \"{0}\";'.format(site)
    with conn:
        response = conn.execute(sql)
    contents = response.fetchall()
    df = pd.DataFrame(contents, columns = ['date', 'Position_m'])
    df['datetime'] = pd.to_datetime(df['date'])
    df['Position_mm'] = df['Position_m'] * 1000
    mindf = df.loc[df.date >= min_date]
    return mindf


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
