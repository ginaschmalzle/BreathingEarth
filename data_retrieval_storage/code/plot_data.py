import matplotlib.pyplot as plt

def plot_data(df, results, site):
    fig, ax = plt.subplots(figsize=(8,6))
    ax.plot(df['Dec_Date'], df['Up'], 'o', label='Up vel')
    ax.plot(df['Dec_Date'], results.fittedvalues, 'r--', linewidth = 4, label='OLS')
    ax.plot(df['Dec_Date'], df['rolling_mean'], linewidth = 6, label='rolling_mean')
    plt.xlabel(site)
    plt.show()
