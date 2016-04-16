import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime as dt
import time
import statsmodels.api as sm

event = { 'site' : 'P020' }
download = True  # False for testing only

def get_velocities(site, download):
    if download == True:
        os.system('wget ftp://data-out.unavco.org/pub/products/position/{0}/{0}.pbo.final_nam08.pos'.format(site))

def read_csv_contents(velo_filename):
    with open(velo_filename, 'r') as f:
        lines = []
        for row in f:
            splitrows = row.split()
            lines.append(splitrows)
    return lines[36:]

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
    df_small = pd.concat([df['Date'], df['Up'], df['Sig']], axis = 1, keys =['Date', 'Up', 'Sig'])
    return df

def ols_model(df):
    model = sm.OLS(df['Dec_Date'], df['Up'])
    results = model.fit()

def run(event):
    site = event['site']
    get_velocities(site, download)
    lines = read_csv_contents('{0}.pbo.final_nam08.pos'.format(site))
    df = get_dataframe(lines)




    # df = pd.read_csv(velo_filename, sep='\t', )
