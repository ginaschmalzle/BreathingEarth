import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime as dt
import time
import statsmodels.api as sm
import numpy as np
import boto
import boto.dynamodb2
from boto.dynamodb2.table import Table
import decimal

event = { 'site' : 'ALBH' }
download = True  # False for testing only

def get_velocities(site, download):
    if download == True:
        os.system('wget ftp://data-out.unavco.org/pub/products/position/{0}/{0}.pbo.final_nam08.pos'.format(site))

def read_csv_contents(velo_filename, site):
    with open(velo_filename, 'r') as f:
        lines = []
        for row in f:
            splitrows = row.split()
            lines.append(splitrows)
    coordinate_data = { 'site' : site,
                        'lat' :decimal.Decimal(lines[8][4]),
                        'lon' :decimal.Decimal(lines[8][5])}
    return lines[36:], coordinate_data

def toYearFraction(date):
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

def get_dataframe(lines):
    headers = lines[0]
    df = pd.DataFrame(lines[1:], columns = lines[0])
    df['Date'] = pd.to_datetime(df['*YYYYMMDD'])
    times = []
    for date in df['Date']:
        times.append(toYearFraction(date))
    df['Dec_Date'] = times
    df['Up'] = pd.to_numeric(df['dU'])
    df['Sig'] = pd.to_numeric(df['Su'])
    df['rolling_mean'] = pd.stats.moments.rolling_mean(df['Up'],7)
    df['rolling_median'] = pd.stats.moments.rolling_median(df['Up'],7)
    df_small = pd.concat([df['Date'], df['Up'], df['Sig']], axis = 1, keys =['Date', 'Up', 'Sig'])
    return df

def ols_model(df, site):
    x = df['Dec_Date']
    model = np.column_stack((x, np.sin(2*np.pi*x), np.cos(2*np.pi*x), np.sin(4*np.pi*x), np.cos(4*np.pi*x)))
    res = sm.OLS(df['Up'], model).fit()
    params = res.params
    params_data = {'site' : site}
    params_data.update({'v' : str(params[0]) })
    params_data.update({'U1' : str(params[1]) })
    params_data.update({'U2' : str(params[2]) })
    params_data.update({'U3' : str(params[3]) })
    params_data.update({'U4' : str(params[4]) })
    return res, params_data

def plot_data(df, results, site):
    fig, ax = plt.subplots(figsize=(8,6))
    ax.plot(df['Dec_Date'], df['Up'], 'o', label='Up vel')
    ax.plot(df['Dec_Date'], results.fittedvalues, 'r--', linewidth = 4, label='OLS')
    ax.plot(df['Dec_Date'], df['rolling_mean'], linewidth = 6, label='rolling_mean')
    plt.xlabel(site)
    plt.show()

def get_dynamo_conn():
    conn = boto.dynamodb2.connect_to_region('us-west-2', aws_access_key_id = os.environ['AWSKEY'], aws_secret_access_key = os.environ['AWSSECRET'])
    return conn

def send_coordinates(conn, coordinate_data):
    site_coordinates = Table('site_coordinates', connection = conn)
    site_coordinates.put_item(data = coordinate_data)

def send_params(conn, params_data):
    model_params = Table('model_parameters', connection = conn)
    model_params.put_item(data = params_data)

def send_vels(conn, df, site):
    vel_data = { 'site' : site }
    for i in range(0, len(df['Date'])):
        vel_data.update({str(df['Date'][i]):[str(df['Up'][i]), str(df['Sig'][i])] })
    vels_table = Table('vertical_velocities', connection = conn)
    vels_table.put_item(data = vel_data)

def run(event):
    start = time.time()
    site = event['site']
    print (site)
    get_velocities(site, download)
    lines, coordinate_data = read_csv_contents('{0}.pbo.final_nam08.pos'.format(site), site)
    df = get_dataframe(lines)
    results, params_data = ols_model(df, site)
    conn = get_dynamo_conn()
    send_coordinates(conn, coordinate_data)
    send_params(conn, params_data)
    send_vels(conn, df, site)
    end = time.time()
    print ('It took {0} seconds to complete tasks.'.format(end-start))




    # df = pd.read_csv(velo_filename, sep='\t', )
