import numpy as np
import statsmodels.api as sm
from utils import toYearFraction


def ols_model(df, site):
    x = df['Dec_Date']
    model = np.column_stack((x, np.sin(2*np.pi*x), np.cos(2*np.pi*x), np.sin(4*np.pi*x), np.cos(4*np.pi*x)))
    res = sm.OLS(df['Up'], model).fit()
    params = res.params
    params_data = {'site' : site}
    params_data.update({'v' : str(params[0]) })
    params_data.update({'U1' : str(params[1]) })
    params_data.update({'U2' : str(params[2]) })
    params_data.update({'U3' : str(params[3]) })
    params_data.update({'U4' : str(params[4]) })
    return res, params_data
