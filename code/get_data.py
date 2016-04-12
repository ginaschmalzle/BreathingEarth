import os
import pandas ad pd

velo_filename = 'pbo.final_nam08.vel'

def get_velocities(filename, download):
    if download == 'yes':
        os.system('wget ftp://data-out.unavco.org/pub/products/velocity/{0}'.format(filename))

def read_csv_contents(velo_filename):
    with open(velo_filename, 'r') as f:
        lines = []
        for row in f:
            splitrows = row.split()
            lines.append(splitrows)
            print splitrows[0]
    return lines

def run():
    #get_velocities(velo_filename, 'yes')



    df = pd.read_csv(velo_filename, sep='\t', )
