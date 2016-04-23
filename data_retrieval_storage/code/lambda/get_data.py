import os
import pandas as pd
import time
import numpy as np
import boto
import boto.dynamodb2
from boto.dynamodb2.table import Table
import decimal

'''
example event, if run locally:

event = { 'site' : 'ALBH',
          'problem_site' : False,
          'environment' : 'local' }

example event if run as a lambda:

event = { 'site' : 'ALBH',
          'problem_site' : False }

'''

def my_handler(event, context):
    download = True  # False for testing only

    def get_velocities(site, download):
        '''Download positions from UNAVCO FTP site'''
        if download == True:
            os.system('wget ftp://data-out.unavco.org/pub/products/position/{0}/{0}.pbo.final_nam08.pos'.format(site))

    def read_csv_contents(velo_filename, site):
        ''' Read contents of csv and format for a dataframe.  Also collect site coordinates.'''
        with open(velo_filename, 'r') as f:
            lines = []
            for row in f:
                splitrows = row.split()
                lines.append(splitrows)
        coordinate_data = { 'site' : site,
                            'lat' :decimal.Decimal(lines[8][4]),
                            'lon' :decimal.Decimal(lines[8][5])}
        return lines[36:], coordinate_data


    def get_dataframe(lines):
        ''' Define dataframe.  Also modify some columns to the correct data type. '''
        headers = lines[0]
        df = pd.DataFrame(lines[1:], columns = lines[0])
        df['Date'] = pd.to_datetime(df['*YYYYMMDD'])
        df['Up'] = pd.to_numeric(df['dU'])
        df['Sig'] = pd.to_numeric(df['Su'])
        df['rolling_mean'] = pd.stats.moments.rolling_mean(df['Up'],7)
        df['rolling_median'] = pd.stats.moments.rolling_median(df['Up'],7)
        df_small = pd.concat([df['Date'], df['Up'], df['Sig']], axis = 1, keys =['Date', 'Up', 'Sig'])
        return df

    def get_dynamo_conn(event):
        ''' Get connection to Dynamo DB.  AWS keys stored as environment variables if run locally.
        event['environment'] does not need to be stated if running on lambda.'''
        try:
            if event['environment'] == 'local':
                conn = boto.dynamodb2.connect_to_region('us-west-2',
                                                        aws_access_key_id = os.environ['AWSKEY'],
                                                        aws_secret_access_key = os.environ['AWSSECRET'])
        except:
                conn = boto.dynamodb2.connect_to_region('us-west-2')
        return conn

    def send_coordinates(conn, coordinate_data):
        '''Send site coordinates to coordinate table'''
        site_coordinates = Table('site_coordinates', connection = conn)
        try:
            site_coordinates.put_item(data = coordinate_data)
        except:
            print ('Site already in DB, updating values if different.')
            item = site_coordinates.get_item(site = coordinate_data['site'])
            update = False
            if coordinate_data['lat'] != item['lat']:
                item['lat'] = coordinate_data['lat']
                update = True
            if coordinate_data['lon'] != item['lon']:
                item['lon'] = coordinate_data['lon']
                update = True
            if update == True:
                print ('Old values differ from new.  Updating coordinates for site {0}'.format(coordinate_data['site']))
                item.partial_save()
            if update == False:
                print ('Items are the same, no change for site {0}'.format(coordinate_data['site']))


    def send_vels(conn, df, site):
        '''Send velocity observations and their uncertainties to the velocity table. Function
        checks if item exists.  If it exists, it check to see if it needs an update.  If it does
        then the item is updated. Otherwise it is left alone. '''
        vel_data = { 'site' : site }
        for i in range(0, len(df['Date'])):
            vel_data.update({str(df['Date'][i]):[{ 'vel' : str(df['Up'][i]),
                                                   'uncert' : str(df['Sig'][i])
                                                 }] })
        vels_table = Table('vertical_velocities', connection = conn)
        try:
            vels_table.put_item(data = vel_data)
        except:
            print ('Site already in DB, updating values.')
            item = vels_table.get_item(site=site)
            keys = vel_data.keys()
            update = False
            for key in keys:
                try:
                    if item[key] != vel_data[key]:
                        item[key] = vel_data[key]
                        update = True
                except:
                    item[key] = vel_data[key]
                    update = True
            if update == True:
                item.partial_save()
                print ('Velocities for site {0} updated'.format(site))
            else:
                print ('No need to update velocities for site {0}'.format(site))


    def send_medians(conn, df, site, coordinate_data):
        '''Send calculated rolling medians to medians table. Function
        checks if item exists.  If it exists, it check to see if it needs an update.  If it does
        then the item is updated. Otherwise it is left alone.'''
        med_data = { 'site' : site }
        lat = coordinate_data['lat']; lon = coordinate_data['lon']
        if lon >= 232. and lon <= 242:
            if lat >= 42 and lat <= 49:
                med_data.update({ 'region' : 'pnw' })
            else:
                med_data.update({ 'region' : 'other' })
        med_data.update({ 'problem_site' :  False })
        for i in range(0, len(df['Date'])):
            med_data.update({str(df['Date'][i]): str(df['rolling_median'][i])})
        median_table = Table('median_velocities', connection = conn)
        try:
            median_table.put_item(data = med_data)
        except:
            print ('Site already in DB, updating values.')
            item = median_table.get_item(region='pnw', site=site)
            keys = med_data.keys()
            update = False
            for key in keys:
                try:
                    if item[key] != med_data[key]:
                        item[key] = med_data[key]
                        update = True
                except:
                    item[key] = med_data[key]
                    update = True
            if update == True:
                item.partial_save()
                print ('Rolling Median for site {0} updated'.format(site))
            else:
                print ('No need to update rolling median for site {0}'.format(site))

    def run(event):
        '''Collect site data, create dataframe, estimate the rolling median and send to
        appropriate tables.'''
        start = time.time()
        site = event['site']
        print (site)
        get_velocities(site, download)
        lines, coordinate_data = read_csv_contents('{0}.pbo.final_nam08.pos'.format(site), site)
        df = get_dataframe(lines)
        # results, params_data = ols_model(df, site)
        conn = get_dynamo_conn()
        send_coordinates(conn, coordinate_data)
        # send_params(conn, params_data)
        send_vels(conn, df, site)
        send_medians(conn, df, site, coordinate_data)
        end = time.time()
        message = 'It took {0} seconds to complete tasks.'.format(end-start)
        return message
    message = run(event)
    return { 'message' :  message }
