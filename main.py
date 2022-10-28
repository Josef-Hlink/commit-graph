import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import make_interp_spline
from scipy.signal import savgol_filter 


def main() -> None:
    username = 'Josef-Hlink'
    contributions = get_contributions(username)
    plot = plot_contributions(contributions)
    plot.savefig('contributions.png', dpi=300)
    return


def get_contributions(username: str) -> pd.DataFrame:
    """ For a username, get the contributions for last year in the form of a pandas DataFrame """
    
    url = f'https://github.com/{username}'
    html = requests.get(url).text
    soup = BeautifulSoup(html, 'html.parser')
    graph = soup.find('div', {'class': 'js-yearly-contributions'})
    data = graph.find_all('rect', {'class': 'ContributionCalendar-day'})

    contributions = pd.DataFrame(columns=['contributions'], dtype='int64')
    contributions.index.name = 'date'

    for item in data:
        n_contributions = int(item.get('data-count', default=0))
        date = item.get('data-date')
        if date:
            contributions.loc[date] = n_contributions
    
    # parse dates in index
    contributions.index = pd.to_datetime(contributions.index)
    
    return contributions


def plot_contributions(contributions: pd.DataFrame) -> plt.Figure:
    """ Create a violinplot where each day of the week is a body  """
    
    contributions['day_of_week'] = contributions.index.dayofweek
    data = contributions.groupby('day_of_week')['contributions'].apply(list).values

    # create figure
    fig, ax = plt.subplots(figsize=(5, 3))
    vp = ax.violinplot(
        data,
        showmeans = False,
        showmedians = False,
        showextrema = False,
        bw_method = 0.4
    )

    for body in vp['bodies']:
        body.set_color('#69c16e')
        body.set_edgecolor('black')
        body.set_linewidth(1)
        body.set_alpha(1)

    for i, points in enumerate(data):
        ax.scatter(
            [i+1] * len(points),
            points,
            marker = 'o',
            color = 'white',
            edgecolor = 'black',
            alpha = 0.25,
            s = 5,
        )
    
    # plot means of data
    means = contributions.groupby('day_of_week').mean()
    ax.scatter(
        means.index + 1,
        means['contributions'],
        marker = 'o',
        color = 'darkgrey',
        edgecolor = 'black',
        s = 25,
        alpha = 0.5
    )

    means_list = means['contributions'].to_list()

    # plot smoothed mean
    smoother = savgol_filter(means_list, 3, 2)
    x_ = np.linspace(1, 7, 100)
    spl = make_interp_spline(means.index + 1, smoother, k=3)
    power_smooth = spl(x_)
    ax.plot(
        x_,
        power_smooth,
        color = 'black',
        linewidth = 1,
        linestyle = '--',
        alpha = 0.75
    )

    ax.set_xticks(range(1, 8))
    ax.set_xticklabels(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'])
    ax.set_xlabel('day of week')
    ax.set_yticks(range(0, 15, 3))
    ax.set_ylabel('contributions')
    ax.set_title('Contributions per day of week')
    fig.tight_layout()

    return fig


if __name__ == '__main__':
    main()
