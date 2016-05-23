import MySQLdb
import boto.rds
import boto
import decimal
import os
import pandas as pd
import numpy
import csv

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

def get_positions(site, download):
    '''Download positions from UNAVCO FTP site'''
    if download == True:
        os.system('wget ftp://data-out.unavco.org/pub/products/position/{0}/{0}.pbo.final_nam08.pos'.format(site))

def get_dataframe(lines, site):
    ''' Define dataframe.  Also modify some columns to the correct data type. '''
    headers = lines[0]
    df = pd.DataFrame(lines[1:], columns = lines[0])
    size = len(df)
    sites = []
    for i in range(0, size):
        sites.append(site)
    df['site'] = sites
    df['Date'] = pd.to_datetime(df['*YYYYMMDD'])
    df['Up'] = pd.to_numeric(df['dU'])
    df['Sig'] = pd.to_numeric(df['Su'])
    df['rolling_median'] = pd.stats.moments.rolling_median(df['Up'],7)
    df_positions = pd.concat([df['site'], df['Date'], df['Up'], df['Sig']], axis = 1, keys =['site','Date', 'Up', 'Sig'])
    df_medians = pd.concat([df['site'], df['Date'], df['rolling_median']], axis = 1, keys =['site', 'Date', 'rolling_median'])
    return df_positions, df_medians

def read_csv_contents(pos_filename, site):
    ''' Read contents of csv and format for a dataframe.  Also collect site coordinates.'''
    with open(pos_filename, 'r') as f:
        lines = []
        for row in f:
            splitrows = row.split()
            lines.append(splitrows)
    coordinate_data = { 'site' : site,
                        'lat' :decimal.Decimal(lines[8][4]),
                        'lon' :decimal.Decimal(lines[8][5])}
    return lines[36:], coordinate_data

def send_latlon_to_db(lat, lon, site, conn):
    sql = 'INSERT INTO coordinates (site, lat, lng) VALUES ("{0}",{1},{2});'.format(site, lat, lon)
    with conn:
        cursor = conn.cursor()
        try:
            cursor.execute(sql)
        except Exception as e:
            print e
    return

def send_pos_to_db(df, conn):
    with conn:
        cursor = conn.cursor()
        try:
            for i, row in df.iterrows():
                values = row.values
                site = values[0]; ts = str(values[1])
                du = values[2]; sig = values[3]
                sql = 'INSERT INTO observations (site, Date, Up, Sig) VALUES ("{0}","{1}",{2},{3});'.format(site, ts, du, sig)
                try:
                    cursor.execute(sql)
                except:
                    pass
        except Exception as e:
            print e
    return

def send_med_to_db(df, conn):
    with conn:
        cursor = conn.cursor()
        try:
            for i, row in df.iterrows():
                values = row.values
                site = values[0]; ts = str(values[1])
                du = values[2]
                if numpy.isnan(du) == False:
                    mytuple = (site, ts, du)
                    sql = 'INSERT INTO medians (site, Date, rolling_median) VALUES {0};'.format(mytuple)
                    cursor.execute(sql)
        except Exception as e:
            print e
    return

def remove_site_file(site):
    filename = '{0}.pbo.final_nam08.pos'.format(site)
    os.system('rm {0}'.format(filename))

def get_weather_data(filename = '../../KSEA_wunderground_data/weather_data/ksea.csv'):
    with open(filename, 'rb') as f:
        myreader = csv.reader(f, delimiter=',')
        header = (myreader.next())
        for i in range(0, len(header)):
            if ' ' in header[i]:
                header[i] = header[i].replace(' ', '')
        lines = [];
        for line in myreader:
            lines.append(tuple(line))
    return lines, tuple(header)

def send_weather_data_to_db(conn):
    data, header = get_weather_data()
    sql = 'INSERT INTO weather {0} VALUES {1};'
    with conn:
        cursor = conn.cursor()
        try:
            for line in data:
                cursor.execute(sql.format(str(header), str(line)))
        except Exception as e:
            print e
    return

def get_db_conn():
    c = boto.rds.RDSConnection(os.environ['AWSKEY'], os.environ['AWSSECRET'])
    dbinstances = c.get_all_dbinstances()
    db = dbinstances[0]
    conn = MySQLdb.connect(host = db.endpoint[0],
                           port = db.endpoint[1],
                           user=os.environ['RDSUSER'],
                           passwd = os.environ['RDSPASS'],
                           db = db.DBName)
    return conn

def run():
    sites = get_sites()
    download = True
    conn = get_db_conn()
    for site in sites:
        try:
            print ('Getting site {0}'.format(site))
            get_positions(site, download)
            lines, coordinate_data = read_csv_contents('{0}.pbo.final_nam08.pos'.format(site), site)
            lat = coordinate_data['lat']; lon = coordinate_data['lon']
            send_latlon_to_db(lat, lon, site, conn)
            print ('Getting dfs')
            df_positions, df_medians = get_dataframe(lines,site)
            print ('Got dfs')
            send_pos_to_db(df_positions, conn)
            print ('Sent pos to db')
            send_med_to_db(df_medians, conn)
            print ('Sent meds to db')
            remove_site_file(site)
        except Exception as e:
            print e
