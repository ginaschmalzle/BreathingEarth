from flask import Flask, jsonify
application = Flask(__name__)
import boto
import boto.dynamodb2
from boto.dynamodb2.table import Table

def get_dynamo_conn(environment = 'local'):
    ''' Get connection to Dynamo DB.  AWS keys stored as environment variables if run locally.
    'environment' does not need to be stated if running on lambda.'''
    try:
        if event['environment'] == 'local':
            conn = boto.dynamodb2.connect_to_region('us-west-2',
                                                    aws_access_key_id = os.environ['AWSKEY'],
                                                    aws_secret_access_key = os.environ['AWSSECRET'])
    except:
            conn = boto.dynamodb2.connect_to_region('us-west-2')
    return conn

def get_site_obs(conn, site):
    obs_table = Table('vertical_positions', connection = conn)
    item = obs_table.get_item(site = site)
    item_keys = item.keys(); item_values = item.values()
    item_dict = {}
    for i in range(0, len(item_keys)):
        if item_keys[i] != 'site':
            try:
                item_dict.update({ item_keys[i]:item_values[i][0]['pos'] })
            except:
                sleep(3)
                item_dict.update({ item_keys[i]:item_values[i][0]['pos'] })
    return item_dict

conn = get_dynamo_conn()

@application.route('/<site>')
def hello(site):
    stuff = get_site_obs(conn, site)
    return jsonify(stuff)

if __name__ == '__main__':
    application.run()
