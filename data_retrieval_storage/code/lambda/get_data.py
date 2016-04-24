import os
import pandas as pd
import time
import boto
import boto.dynamodb2
from boto.dynamodb2.table import Table
import decimal
# import subprocess

'''
example event, if run locally:

event = { 'site' : 'ALBH',
          'problem_site' : False,
          'environment' : 'local' }

example event if run as a lambda:

event = { 'site' : 'ALBH',
          'problem_site' : False }

'''

# SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# LIB_DIR = os.path.join(SCRIPT_DIR, 'lib')

def my_handler(event, context):
    download = True  # False for testing only

    def get_positions(site, download):
        '''Download positions from UNAVCO FTP site'''
        if download == True:
            os.system('wget ftp://data-out.unavco.org/pub/products/position/{0}/{0}.pbo.final_nam08.pos'.format(site))

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


    def send_pos(conn, df, site):
        '''Send position observations and their uncertainties to the position table. Function
        checks if item exists.  If it exists, it check to see if it needs an update.  If it does
        then the item is updated. Otherwise it is left alone. '''
        pos_data = { 'site' : site }
        for i in range(0, len(df['Date'])):
            pos_data.update({str(df['Date'][i]):[{ 'pos' : str(df['Up'][i]),
                                                   'uncert' : str(df['Sig'][i])
                                                 }] })
        pos_table = Table('vertical_positions', connection = conn)
        try:
            pos_table.put_item(data = pos_data)
        except:
            print ('Site already in DB, updating values.')
            item = pos_table.get_item(site=site)
            keys = pos_data.keys()
            update = False
            for key in keys:
                try:
                    if item[key] != pos_data[key]:
                        item[key] = pos_data[key]
                        update = True
                except:
                    item[key] = pos_data[key]
                    update = True
            if update == True:
                item.partial_save()
                print ('Positions for site {0} updated'.format(site))
            else:
                print ('No need to update Positions for site {0}'.format(site))


    def send_medians(conn, df, site, coordinate_data):
        '''Send calculated rolling medians to medians table. Function
        checks if item exists.  If it exists, it check to see if it needs an update.  If it does
        then the item is updated. Otherwise it is left alone.'''
        med_data = { 'site' : site }
        lat = coordinate_data['lat']; lon = coordinate_data['lon']
        if lon >= 232. and lon <= 242.:
            if lat >= 40. and lat <= 50.:
                med_data.update({ 'region' : 'pnw' })
            else:
                med_data.update({ 'region' : 'other' })
        else:
            med_data.update({ 'region' : 'other' })
        med_data.update({ 'problem_site' :  False })
        for i in range(0, len(df['Date'])):
            med_data.update({str(df['Date'][i]): str(df['rolling_median'][i])})
        print ('Site = {0}'.format(site))
        print ('med_data region = {0}'.format(str(med_data['region'])))
        print ('med_data site = {0}'.format(str(med_data['site'])))
        median_table = Table('median_positions', connection = conn)
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

    def remove_site_file(site):
        filename = '{0}.pbo.final_nam08.pos'.format(site)
        os.system('rm {0}'.format(filename))

    def run(event):
        '''Collect site data, create dataframe, estimate the rolling median and send to
        appropriate tables.'''
        conn = get_dynamo_conn(event)
        start = time.time()
        site = event['site']
        get_positions(site, download)
        lines, coordinate_data = read_csv_contents('{0}.pbo.final_nam08.pos'.format(site), site)
        lat = coordinate_data['lat']; lon = coordinate_data['lon']
        if lon >= 232. and lon <= 242.:
            if lat >= 40. and lat <= 50.:
                print ('Getting info from {0} at {1} lat, {2} lon.'.format(site, str(lat), str(lon)))
                df = get_dataframe(lines)
                send_coordinates(conn, coordinate_data)
                send_pos(conn, df, site)
                send_medians(conn, df, site, coordinate_data)
        else:
            print ('Site {0} not in range at {1} lat, {2} lon.'.format(site, str(lat), str(lon)))
        remove_site_file(site)
        end = time.time()
        message = 'It took {0} seconds to complete tasks.'.format(end-start)
        return message
    message = run(event)
    return { 'message' :  message }
