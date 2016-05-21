import os


def get_weather(y, m, site):
    '''Download weather from wunderground'''
    os.system('wget https://www.wunderground.com/history/airport/{0}/{1}/{2}/4/MonthlyHistory.html?req_city=&req_state=&req_statename=&reqdb.zip=&reqdb.magic=&reqdb.wmo=&format=1'.format(site,y,m))

def run():
    years = range(2008,2017)
    months = range(1,13)
    site = 'KSEA'
    for y in years:
        for m in months:
            get_weather(y, m, site)
