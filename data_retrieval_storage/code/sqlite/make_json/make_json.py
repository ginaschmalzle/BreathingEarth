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

def make_dict_of_medians(start_site_dict, problem_sites, start_time, end_time, time_step, coordinate_dict, bounds, conn):
    start_time_dt = datetime.datetime.strptime(start_time, '%Y-%m-%d 00:00:00')
    end_time_dt = datetime.datetime.strptime(end_time, '%Y-%m-%d 00:00:00')
    time_dt = start_time_dt
    sites = start_site_dict.keys()
    no_problem_sites = tuple([x for x in sites if x not in problem_sites])
    response_list = []; median_dict = {}
    [minlat, maxlat, minlon, maxlon] = bounds
    with conn:
        while time_dt < end_time_dt:
            time_str = time_dt.strftime('%Y-%m-%d 00:00:00')
            sql = "SELECT m.site, m.date, m.rolling_median, c.lat, c.lng FROM medians m \
                   INNER JOIN coordinates c\
                   ON c.site = m.site \
                   WHERE Date = \"{0}\" \
                   AND c.lat >= {1} \
                   AND c.lat <= {2} \
                   AND c.lng >= {3} \
                   AND c.lng <= {4} \
                   AND m.site IN {5}".format(time_str,
                                           minlat,
                                           maxlat,
                                           minlon,
                                           maxlon,
                                           str(no_problem_sites))
            r = conn.execute(sql)
            response_list.append(r.fetchall())
            time_dt = time_dt + datetime.timedelta(days = time_step)
    for response in response_list:
        response_site = response[0][0]
        coords = coordinate_dict[response_site]
        response_date = response[0][1]
        median_dict[response_date] = {}
        for line in response:
            print line
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
                                            "lng" : line[2] }})
    return coordinate_dict


def get_ts_from_site(conn, site):
    sql = 'SELECT * FROM {0} WHERE site = \"{1}\"'
    tables = ['positions', 'medians']
    pos_list = []; med_list = []
    for t in tables:
        with conn:
            response = conn.execute(sql.format(t, site))
        if t == 'positions':
            positions = response.fetchall()
        else:
            medians = response.fetchall()
    for item in positions:
        pos_list.append([item[1][:10], item[2] * 1000])
    for item in medians:
        med_list.append([item[1][:10], item[2] * 1000])
    return pos_list, med_list


def run():
    db = '../populate_tables/breathingearth.db'
    conn = sqlite3.connect(db)
    start_time = '2008-01-01 00:00:00'
    end_time = '2016-05-01 00:00:00'
    time_step = 30
    start_medians = get_median_starts(conn)
    start_site_dict = get_start_site_dict(start_medians)

    coordinate_dict = get_coordinates(tuple(start_site_dict.keys()))
    coord_filename = '../../../data/coordinates_sqlite.json'
    write_json_to_file(coord_filename, coordinate_dict)

    pnw_bounds = [40, 50, 230, 243]
    sw_bounds = [30, 40, 234, 246]
    alaska_bounds = [53, 71, 181, 230]
    pnw_median_dict = make_dict_of_medians(start_site_dict,
                                       problem_sites,
                                       start_time,
                                       end_time,
                                       time_step,
                                       coordinate_dict,
                                       pnw_bounds,
                                       conn)
    sw_median_dict = make_dict_of_medians(start_site_dict,
                                       problem_sites,
                                       start_time,
                                       end_time,
                                       time_step,
                                       coordinate_dict,
                                       sw_bounds,
                                       conn)
    alaska_median_dict = make_dict_of_medians(start_site_dict,
                                       problem_sites,
                                       start_time,
                                       end_time,
                                       time_step,
                                       coordinate_dict,
                                       alaska_bounds,
                                       conn)
    pnw_med_filename = '../../../data/positions_sample_size_{0}_sqlite_pnw.json'.format(str(time_step))
    sw_med_filename = '../../../data/positions_sample_size_{0}_sqlite_sw.json'.format(str(time_step))
    alaska_med_filename = '../../../data/positions_sample_size_{0}_sqlite_alaska.json'.format(str(time_step))
    write_json_to_file(pnw_med_filename, pnw_median_dict)
    write_json_to_file(sw_med_filename, sw_median_dict)
    write_json_to_file(alaska_med_filename, alaska_median_dict)


    positions, medians = get_ts_from_site(conn, site)
    ts_filename = '../../../data/{0}_ts.dat'.format(site)
    ts_dict = { 'positions': positions, 'medians': medians }
    write_json_to_file(ts_filename, ts_dict)
