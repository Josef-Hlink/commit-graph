import argparse
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from scipy.interpolate import make_interp_spline
from scipy.signal import savgol_filter 


def main() -> None:
    
    parser = argparse.ArgumentParser()
    parser.add_argument('username', type=str, help='Github username')
    args = parser.parse_args()
    username = args.username

    contributions = get_contributions(username)
    plot = plot_contributions(contributions, username)
    plot.savefig('contributions.png', dpi=300)
    
    return


def get_contributions(username: str) -> pd.DataFrame:
    """ For a username, get the contributions for last year in the form of a pandas DataFrame """
    
    # get contribution graph data
    url = f'https://github.com/{username}'
    html = requests.get(url).text
    if html == 'Not Found':
        raise ValueError(f'User "{username}" not found on GitHub')
    soup = BeautifulSoup(html, 'html.parser')
    graph = soup.find('div', {'class': 'js-yearly-contributions'})
    data = graph.find_all('rect', {'class': 'ContributionCalendar-day'})

    contributions = pd.DataFrame(columns=['contributions'], dtype='int64')
    contributions.index.name = 'date'

    for item in data:
        if not item.text: continue
        n_contributions = int(first) if (first := item.text.split(' ')[0]) != 'No' else 0
        date = item.get('data-date')
        if date:
            contributions.loc[date] = n_contributions
    
    # check if plotting will work
    if contributions['contributions'].max() == 0:
        raise ValueError(f'No contributions for the last year could be found for user: {username}')
    
    # parse dates in index
    contributions.index = pd.to_datetime(contributions.index)
    
    return contributions


def plot_contributions(contributions: pd.DataFrame, username: str) -> plt.Figure:
    """ Create a violinplot where each day of the week is a body  """

    start, end = contributions.index[0], contributions.index[-1]
    contributions['day_of_week'] = contributions.index.dayofweek
    data = contributions.groupby('day_of_week')['contributions'].apply(list).values
    max_contributions = contributions['contributions'].max()
    colors = [
        '#ace7ae',  # light green
        '#69c16e',  # slightly darker green
        '#539f57',  # "normal" green
        '#386c3e'   # dark green
    ]

    # create figure
    fig, ax = plt.subplots(figsize=(5, 3))

    ax = add_violins(ax, data, colors)
    ax = add_means(ax, contributions)
    ax = fix_layout(ax, max_contributions)
    ax.set_title(f'Contributions per day of week ({username})')
    
    fig = add_timeframe(fig, start, end)
    fig.tight_layout()
    
    return fig


def add_violins(ax: plt.Axes, data: list, colors: list[str]) -> plt.Axes:
    """ Add violins to the axes object """
    
    vp = ax.violinplot(
        data,
        showmeans = False,
        showmedians = False,
        showextrema = False,
        widths = 0.8,
        bw_method = 0.4
    )

    means = [np.mean(d) for d in data]
    classes = np.linspace(np.min(means), np.max(means), 4)
    cmap = list(zip(classes, colors))

    for i, body in enumerate(vp['bodies']):
        mean = means[i]
        for c, color in cmap:
            if mean <= c:
                body.set_facecolor(color)
                break
        body.set_edgecolor('black')
        body.set_linewidth(.5)
        body.set_alpha(1)

    return ax

def add_means(ax: plt.Axes, contributions: pd.DataFrame) -> plt.Axes:
    """ Add means to the axes object """
    
    means = contributions.groupby('day_of_week').mean()
    
    # raw mean points
    ax.scatter(
        means.index + 1,
        means['contributions'],
        marker = 'o',
        color = 'darkgrey',
        edgecolor = 'black',
        s = 25,
        alpha = 0.5
    )

    # smoothed mean
    smoother = savgol_filter(means['contributions'].to_list(), 3, 2)
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

    return ax

def fix_layout(ax: plt.Axes, max_c: int) -> plt.Axes:
    """ Fix the layout of the axes object """
    
    # background
    ax.set_facecolor('#ebedf0')
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_axisbelow(True)
    ax.yaxis.grid(color='white', linestyle='-', linewidth=2)
    
    # axes ticks & labels
    ax.set_xticks(range(1, 8))
    ax.set_xticklabels(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'])
    ax.set_ylabel('contributions')
    stepsize = max(max_c // 5, 1)
    ax.set_xlim(0.5, 7.5)
    ax.set_ylim(-(stepsize / 4), max_c + stepsize // 2)
    ax.set_yticks(range(0, max_c, stepsize))
    ax.tick_params(
        axis = 'both',
        bottom = False,
        left = False
    )

    # white rect to "remove" grey area below y=0
    ax.add_patch(
        Rectangle(
            (0, -stepsize),
            8,
            stepsize,
            facecolor = 'white',
            edgecolor = 'none',
            zorder = -1
        )
    )

    return ax

def add_timeframe(fig: plt.Figure, start: pd.Timestamp, end: pd.Timestamp) -> plt.Figure:
    """ Add a timeframe box to the figure """
    
    fig.text(
        0.01,
        0.01,
        f'{start.date()}\n{end.date()}',
        fontsize=6,
        color='white',
        horizontalalignment='left',
        verticalalignment='bottom',
        # center text in textbox
        bbox=dict(
            facecolor='black',
            edgecolor='gray',
            boxstyle='round, pad=0.2'
        )
    )

    return fig


if __name__ == '__main__':
    main()
