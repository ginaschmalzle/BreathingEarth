import sqlite3
import datetime
import json
from  problem_sites import  problem_sites

def get_median_starts(conn, start_time = '2008-01-01 00:00:00'):
    sql = 'SELECT * FROM medians WHERE Date = \"{0}\";'.format(start_time)
    response = ''
    with conn:
        cursor = conn.cursor()
        try:
            response = cursor.execute(sql)
        except Exception as e:
            print (e)
    return response.fetchall()

def get_start_site_dict(start_medians):
    start_site_dict = {}
    for line in start_medians:
        start_site_dict.update({ str(line[0]): line[2]})
    return start_site_dict

def make_dict_of_medians(start_site_dict, problem_sites, start_time, end_time, time_step, conn):
    start_time_dt = datetime.datetime.strptime(start_time, '%Y-%m-%d 00:00:00')
    end_time_dt = datetime.datetime.strptime(end_time, '%Y-%m-%d 00:00:00')
    time_dt = start_time_dt
    sites = start_site_dict.keys()
    no_problem_sites = tuple([x for x in sites if x not in problem_sites])
    response_list = []; median_dict = {}
    with conn:
        while time_dt < end_time_dt:
            time_str = time_dt.strftime('%Y-%m-%d 00:00:00')
            sql = 'SELECT * FROM medians WHERE Date = \"{0}\" AND site IN {1}'.format(time_str, str(no_problem_sites))
            r = conn.execute(sql)
            response_list.append(r.fetchall())
            time_dt = time_dt + datetime.timedelta(days = time_step)
        for response in response_list:
            response_date = response[0][1]
            median_dict[response_date] = {}
            for line in response:
                # print line
                start = float(start_site_dict[line[0]])
                median_dict[response_date].update({ line[0] : float(line[2]) - start })
    return median_dict

def write_json_to_file(filename, mydict):
    with open(filename, 'w') as f:
        json.dump(mydict, f)
    return

def get_coordinates(sites):
    coordinate_dict = {}
    sql = 'SELECT * FROM coordinates WHERE site in {0};'.format(sites)
    with conn:
        r = conn.execute(sql)
        response = r.fetchall()
    for line in response:
        coordinate_dict.update({ line[0]: { "lat" : line[1],
                                            "lon" : line[2] }})
    return coordinate_dict

def run():
    db = '../populate_tables/breathingearth.db'
    conn = sqlite3.connect(db)
    start_time = '2008-01-01 00:00:00'
    end_time = '2016-05-01 00:00:00'
    time_step = 30
    start_medians = get_median_starts(conn)
    start_site_dict = get_start_site_dict(start_medians)
    coordinate_dict = get_coordinates(tuple(start_site_dict.keys()))
    median_dict = make_dict_of_medians(start_site_dict, problem_sites, start_time, end_time, time_step, conn)
    med_filename = '../../../data/positions_sample_size_{0}_sqlite.json'.format(str(time_step))
    write_json_to_file(med_filename, median_dict)
    coord_filename = '../../../data/coordinates_sqlite.json'
    write_json_to_file(coord_filename, coordinate_dict)
