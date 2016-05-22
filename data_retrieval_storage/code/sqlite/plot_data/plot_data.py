import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.ticker import FuncFormatter
import sqlite3
import pandas as pd
import numpy as np
import datetime
import simplekml
import time
from datetime import datetime as dt

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
    content_dict = {}
    for line in content:
        content_dict.update({ line[0]: { 'lat' : line[1],
                                         'lng' : line[2]}})
    return content_dict

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

def make_xlabel(site, coordinate_dict):
    lat = round(coordinate_dict[site]['lat'], 3)
    lon = (360 - round(coordinate_dict[site]['lng'], 3)) * -1
    label ='{0}, Lat = {1} N, Lon = {2} W'.format(site, lat, lon)
    return label

def get_all_sites(conn, min_date):
    sql = 'SELECT * FROM positions;'
    with conn:
        response = conn.execute(sql)
    contents = response.fetchall()
    all_df = pd.DataFrame(contents, columns = ['site', 'date', 'Position_m', 'Sig_m'])
    all_df = all_df.loc[all_df.date >= min_date]
    all_df['datetime'] = pd.to_datetime(all_df['date'])
    all_df['Position_mm'] = all_df['Position_m'] * 1000
    return mindf

def plot_subplot_ts(df, site, coordinate_dict, ax, eq):
    site_df = df.loc[ (df['site'] == site) ]
    times = []
    for t in site_df['datetime']:
        times.append(toYearFraction(t))
    site_df['Dec_time'] = times
    ax.set_title(make_xlabel(site, coordinate_dict))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, pos: '%.0f'%x))
    ax.scatter(site_df['Dec_time'], site_df['Position_mm'], marker = 'o', label='rolling_median')
    ax.plot([2008,2016],[0,0], color = 'red')
    if eq == True:
        ax.plot([2010.2546803652967,2010.2546803652967],[-100,100], color = 'red')
    plt.ylabel('Vertical Position (mm)')

def plot_subset_of_site_ts(df, subset_sites, rows, columns, coordinate_dict, show, filename, eq):
    '''Subset should contain 4 or less sites.'''
    f, plots = plt.subplots(rows, columns, sharex=True, sharey=True)
    plt.xlim(2008.0, 2016.0)
    if eq == False:
        plt.ylim(-150.0, 150.0)
    else:
        plt.ylim(-50.0, 50.0)
    f.set_size_inches(15.,10., forward = True)
    i = 0
    for row in plots:
        for item in row:
            try:
                pl = item
                site = subset_sites[i]
                i = i + 1
                plot_subplot_ts(df, site, coordinate_dict, pl, eq)
            except:
                pass
    plt.savefig(filename, transparent=True)
    if show == True:
        plt.show()

def run():
    db = '../populate_tables/breathingearth.db'
    conn = sqlite3.connect(db)

    # Make kml file for plotting on Google Earth
    coordinate_dict = coordinates_to_kml(conn)

    # Plot single site with weather data
    min_date = '2008-01-01'
    site = 'SEAT'
    site_df = get_single_site(site, conn, min_date)
    precip_df = get_precip(conn)
    monthly_sums = get_monthly_sums(precip_df)
    plot_weather_with_GPSsite(monthly_sums, site, site_df)

    # Plot multiple plots
    eq_sites = ['P498', 'P496', 'P497', 'P744']
    oil_sites = ['ARM1', 'ARM2', 'P545', 'P564']
    glacier_sites = ['AB43', 'AB50', 'ELDC', 'AB44']
    sea_level_sites = ['CCV5', 'CCV6']
    all_df = get_all_sites(conn, min_date)
    rows = 2; columns = 2

    mpl.rcParams.update({'font.size': 12})
    mpl.rcParams['figure.titlesize'] = 'medium'
    for subset_sites in [eq_sites, oil_sites, glacier_sites, sea_level_sites]:
        eq = False
        if subset_sites == eq_sites:
            filename = 'eq_sites.png'
            eq = True
        elif subset_sites == oil_sites:
            filename = 'oil_sites.png'
        elif subset_sites == glacier_sites:
            filename = 'glacier_sites.png'
        elif subset_sites == oil_sites:
            filename = 'sea_level_sites.png'
        else:
            filename = 'no_specification.png'
        plot_subset_of_site_ts(all_df,
                               subset_sites,
                               rows,
                               columns,
                               coordinate_dict,
                               show = False,
                               filename = filename,
                               eq = eq)
