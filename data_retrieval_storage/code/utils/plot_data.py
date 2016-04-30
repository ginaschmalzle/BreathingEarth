import matplotlib.pyplot as plt
import boto
import boto.dynamodb2
from boto.dynamodb2.table import Table
import os
import pandas as pd
from time import sleep
import logging
from datetime import datetime as dt
import numpy as
import datetime
import time
sys.path.insert(0, '../utils/utils.py')
import utils

conn = utils.get_dynamo_conn(environment = 'local')
df = utils.get_medians_df(conn)

def plot_data(df, results, site):
    fig, ax = plt.subplots(figsize=(8,6))
    ax.plot(df['Dec_Date'], df['Up'], 'o', label='Up vel')
    ax.plot(df['Dec_Date'], results.fittedvalues, 'r--', linewidth = 4, label='OLS')
    ax.plot(df['Dec_Date'], df['rolling_mean'], linewidth = 6, label='rolling_mean')
    plt.xlabel(site)
    plt.show()
