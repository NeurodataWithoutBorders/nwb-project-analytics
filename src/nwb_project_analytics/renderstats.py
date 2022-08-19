"""
Module with routines for plotting code and git statistics
"""
from matplotlib import pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as patches
import numpy as np
import warnings
from datetime import datetime, timedelta

from .gitstats import GitHubRepoInfo, NWBGitInfo
from .codecovstats import CodecovInfo


def plot_release_timeline(
        repo_info: GitHubRepoInfo,
        figsize: tuple = None,
        fontsize: int = 14,
        month_intervals: int = 3,
        xlim: tuple = None,
        ax=None,
        title_on_yaxis: bool = False,
        add_releases: list = None):
    """
    Plot a timeline of the releases for the repo

    Based on https://matplotlib.org/stable/gallery/lines_bars_and_markers/timeline.html

    :param repo_info: The GitHubRepoInfo object to plot a release timeline for
    :param figsize: Tuple with the figure size if a new figure is to be created, i.e., if ax is None
    :param fontsize: Fontsize to use for labels (default=14)
    :param month_intervals: Integer indicating the step size in number of month for the y axis
    :param xlim: Optional tuple of datetime objects with the start and end-date for the x axis
    :param ax: Matplotlib axis object to be used for plotting
    :param title_on_yaxis: Show plot title as name of the y-axis (True) or as the main title (False) (default=False)
    :param add_releases: Sometimes libraries did not use git tags to mark releases. With this we can add
                         additional releases that are missing from the git tags.
    :type add_releases: List of tuples with "name: str" and "date: datetime.strptime(d[0:10], "%Y-%m-%d")"

    :return: Matplotlib axis object used for plotting
    """
    names, dates = repo_info.get_release_names_and_dates()
    if add_releases is not None:
        for r in add_releases:
            names.append(r[0])
            dates.append(r[1])

    # Choose some nice levels
    try:
        version_jumps = repo_info.get_version_jump_from_tags(names)
        levels = []
        curr_major = 5
        curr_minor = 2
        curr_patch = -5
        for n in names:
            if version_jumps[n] == "major":
                levels.append(curr_major)
            elif version_jumps[n] == "minor":
                levels.append(curr_minor)
                curr_minor = 2 if curr_minor < 2 else 1
            elif version_jumps[n] == "patch":
                levels.append(curr_patch)
                curr_patch += 1
                if curr_patch > -0.5:  # Check for 0 and loop back to -5
                    curr_patch = -5
        levels_by_version_jumps = True
    except Exception as e:
        warnings.warn("Computing version jumps from tags failed. Fall back to default levels." + str(e))
        levels = np.tile([-5, 5, -3, 3, -1, 1],
                         int(np.ceil(len(dates) / 6)))[:len(dates)]
        levels_by_version_jumps = False

    # Create figure and plot a stem plot with the date
    if ax is None:
        fig, ax = plt.subplots(figsize=(12, 5) if figsize is None else figsize)

    ax.vlines(dates, 0, levels, color="dodgerblue")  # The vertical stems.
    ax.plot(dates, np.zeros_like(dates), "-o",
            color="k", markerfacecolor="w")  # Baseline and markers on it.

    # annotate lines
    for d, l, r in zip(dates, levels, names):
        ax.annotate(r, xy=(d, l),
                    xytext=(fontsize + 2, np.sign(l) * 3), textcoords="offset points",
                    horizontalalignment="right",
                    verticalalignment="bottom" if l > 0 else "top",
                    fontsize=fontsize)

    # format xaxis with 4 month intervals
    if xlim is not None:
        ax.set_xlim(xlim)
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=month_intervals))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right", fontsize=fontsize)

    # set the title
    if title_on_yaxis:
        ax.get_yaxis().set_ticks([])
        ax.set_ylabel(repo_info.repo.repo, fontsize=fontsize)
    else:
        ax.set_title("%s release dates" % repo_info.repo.repo, fontdict={"fontsize": fontsize})
        ax.yaxis.set_visible(False)

    # Set margins and grid lines
    ax.margins(y=0.1)

    # If levels of lines correspond to version jumps, then color code the background and add a legend
    if levels_by_version_jumps:
        # Create a Rectangle patch
        legend_items = []
        # Major releases background
        legend_items.append(patches.Rectangle(xy=(ax.get_xlim()[0], 3.5),  # xy origin
                                              width=ax.get_xlim()[1] - ax.get_xlim()[0],  # width
                                              height=ax.get_ylim()[1] - 3.5,
                                              linewidth=0, facecolor='lightgreen', edgecolor=None))
        # Minor releases background
        legend_items.append(patches.Rectangle(xy=(ax.get_xlim()[0], 0),  # xy origin
                                              width=ax.get_xlim()[1] - ax.get_xlim()[0],  # width
                                              height=3.5,
                                              linewidth=0, facecolor='lightblue', edgecolor=None))
        # Patch releases background
        legend_items.append(patches.Rectangle(xy=(ax.get_xlim()[0], ax.get_ylim()[0]),  # xy origin
                                              width=ax.get_xlim()[1] - ax.get_xlim()[0],  # width
                                              height=abs(ax.get_ylim()[0]),
                                              linewidth=0, facecolor='lightgray', edgecolor=None))
        # Add the patches to plot
        for patch in legend_items:
            ax.add_patch(patch)
        # Add a a legend for the backround color
        ax.legend(legend_items, ['Major', 'Minor', 'Patch'],
                  loc='lower left', fontsize=fontsize, edgecolor='black',
                  facecolor='white', framealpha=1)
    ax.grid(axis="x", linestyle='dashed', color='gray')

    return ax


def plot_multiple_release_timeslines(
        github_repo_infos,
        add_releases: dict = None,
        date_range: tuple = None,
        month_intervals: int = 2,
        fontsize: int = 16,
        title: str = None
        ):
    """

    :param github_repo_infos: GitHubRepoInfo objects to render. For all NWB2 repos set
                        to NWBGitInfo.GIT_REPOS.get_info_objects()
    :type github_repo_infos: OrderdDict (or dict) of GitHubRepoInfo objects
    :param add_releases: Sometimes libraries did not use git tags to mark releases. With this we can add
                        additional releases that are missing from the git tags. If None this is set to
                        NWBGitInfo.MISSING_RELEASE_TAGS by default. Set to empty dict if no additional
                        releases should be added.
    :type add_releases: Dict where the keys are a subset of the keys of the github_repos dict and the values are
                        lists of tuples with "name: str" and "date: datetime.strptime(d[0:10], "%Y-%m-%d")" of
                        additional releases for the given repo. Usually this is set to NWBGitInfo.MISSING_RELEASE_TAGS
    :param date_range: Tuple of datetime objects with the start and stop time to use along the x axis for rendering
                       By default this is set to (NWBGitInfo.NWB2_BETA_RELEASE - timedelta(days=60), datetime.today())
    :param month_intervals: Integer with spacing of month along the x axis. (Default=2)
    :param fontsize: Fontsize to use in the plots
    :return: Tuple of matplotlib figure object and list of axes object used for rendering
    """
    if add_releases is None:
        add_releases = NWBGitInfo.MISSING_RELEASE_TAGS
    if date_range is None:
        date_range = (NWBGitInfo.NWB2_BETA_RELEASE - timedelta(days=60),
                      datetime.today())

    # Render the release timeline for all repos
    fig, axes = plt.subplots(figsize=(16, len(github_repo_infos) * 4.2),
                             nrows=len(github_repo_infos),
                             ncols=1,
                             sharex=True,
                             sharey=False,
                             squeeze=True)
    for i, repo in enumerate(github_repo_infos.keys()):
        ax = plot_release_timeline(
            repo_info=github_repo_infos[repo],
            fontsize=fontsize,
            month_intervals=month_intervals,
            xlim=date_range,
            ax=axes[i],
            title_on_yaxis=True,
            add_releases=add_releases.get(repo, None))
        # Show the legend only on the first plot (since it is the same for all)
        if i > 0:
            # Remove the legend if it exists. The legend may be missing if there are no releases
            if ax.get_legend() is not None:
                ax.get_legend().remove()
    # add the title
    if title is not None:
        axes[0].set_title(title, fontdict={'fontsize': fontsize})

    # Final layout, save, and display
    plt.tight_layout()
    plt.subplots_adjust(wspace=0.0, hspace=0.02)

    return fig, axes


class RenderCodecovInfo:
    """Helper class for plotting CoedcovInfo data """
    @classmethod
    def __plot_single_codecov(cls, codename, timestamps, coverage, plot_xlim, fontsize):
        """Internal helper function used to plot a single codecov  """
        plt.fill_between(timestamps, coverage)
        plt.plot(timestamps, coverage, '--o', color='black')
        if plot_xlim is not None:
            r = np.logical_and(timestamps >= plot_xlim[0], timestamps <= plot_xlim[1])
            plt.ylim(coverage[r].min()-1, coverage[r].max()+1)
            plt.xlim(plot_xlim)
        plt.ylabel("Coverage in %", fontsize=fontsize)
        plt.title(codename, fontsize=fontsize)
        plt.yticks(fontsize=fontsize)
        plt.xticks(fontsize=fontsize, rotation=45)

    @classmethod
    def plot_codecov_individual(cls, codecovs, plot_xlim=None, fontsize=16, basefilename=None):
        """
        Plot coverage results for one or more codes as a sequence of individual figures all of which are
        plotted and saved separately (one per code)

        Example for setting for ``codecovs``:

        .. code:: Python

            codecovs = {r: CodecovInfo.get_pulls_or_commits(NWBGitInfo.GIT_REPOS[r],
                                                            key='commits', state='all',
                                                            branch=NWBGitInfo.GIT_REPOS[r].mainbranch)
                       for r in ['HDMF', 'PyNWB', 'MatNWB']}

        :param codecovs: Dictionary where the keys are the names of the codes and the values are the output from
                         CodecovInfo.get_pulls_or_commits defining the coverage timeline for each code.
        :param plot_xlim: Tuple of datatime objects defining the time-range of the x-axis. E.g.,
                          plot_xlim=(datetime.strptime("2021-01-01", "%Y-%m-%d"), datetime.today())
        :param fontsize: Fontsize to be used for axes label, tickmarks, and titles. (default=16)
        :param basefilename: Base name of the file(s) where the plots should eb saved to. Set to None to
                         only show but not save the plots. Figures will be saved as both PDF and PNG.
                         (default=None)
        """
        # Create separate figure for each code
        i = 0
        for k, v in codecovs.items():
            timestamps, coverage, nocov = CodecovInfo.get_time_and_coverage(v)
            cls.__plot_single_codecov(k, timestamps, coverage, plot_xlim, fontsize)
            i += 1
            plt.tight_layout()
            if basefilename is not None:
                plt.savefig(basefilename + "_" + k + '.pdf', dpi=300)
                plt.savefig(basefilename + "_" + k + '.png', dpi=300)
            plt.show()

    @classmethod
    def plot_codecov_grid(cls, codecovs, plot_xlim=None, fontsize=16, basefilename=None):
        """
        Plot coverage results for one or more codes as a single figure with one row per code so all
        codes appear in their own plots but with a shared x-axis for time and creating only a single file

        Example for setting for ``codecovs``:

        .. code:: Python

            codecovs = {r: CodecovInfo.get_pulls_or_commits(NWBGitInfo.GIT_REPOS[r],
                                                            key='commits', state='all',
                                                            branch=NWBGitInfo.GIT_REPOS[r].mainbranch)
                       for r in ['HDMF', 'PyNWB', 'MatNWB']}

        :param codecovs: Dictionary where the keys are the names of the codes and the values are the output from
                         CodecovInfo.get_pulls_or_commits defining the coverage timeline for each code.
        :param plot_xlim: Tuple of datatime objects defining the time-range of the x-axis. E.g.,
                          plot_xlim=(datetime.strptime("2021-01-01", "%Y-%m-%d"), datetime.today())
        :param fontsize: Fontsize to be used for axes label, tickmarks, and titles. (default=16)
        :param basefilename: Base name of the file(s) where the plots should eb saved to. Set to None to
                         only show but not save the plots. Figures will be saved as both PDF and PNG.
                         (default=None)
        """
        fig, axes = plt.subplots(figsize=(8, len(codecovs)*4.2),
                                 nrows=len(codecovs), ncols=1,
                                 sharex=True, sharey=False,
                                 squeeze=True)
        i = 0
        for k, v in codecovs.items():
            timestamps, coverage, nocov = CodecovInfo.get_time_and_coverage(v)
            ax = axes[i] if len(codecovs) > 1 else axes
            plt.sca(ax)
            cls.__plot_single_codecov(k, timestamps, coverage, plot_xlim, fontsize)
            i += 1
        plt.tight_layout()
        if basefilename is not None:
            plt.savefig(basefilename + '.pdf', dpi=300)
            plt.savefig(basefilename + '.png', dpi=300)
        plt.show()

    @staticmethod
    def plot_codecov_multiline(codecovs, plot_xlim=None, fill_alpha=0.2,  fontsize=16, basefilename=None, figsize=None):
        """
        Plot coverage results for one or more codes as a single figure with each code represented by
        a line plot with optional filled area.

        Example for setting for ``codecovs``:

        .. code:: Python

            codecovs = {r: CodecovInfo.get_pulls_or_commits(NWBGitInfo.GIT_REPOS[r],
                                                            key='commits', state='all',
                                                            branch=NWBGitInfo.GIT_REPOS[r].mainbranch)
                       for r in ['HDMF', 'PyNWB', 'MatNWB']}

        :param codecovs: Dictionary where the keys are the names of the codes and the values are the output from
                         CodecovInfo.get_pulls_or_commits defining the coverage timeline for each code.
        :param plot_xlim: Tuple of datatime objects defining the time-range of the x-axis. E.g.,
                          plot_xlim=(datetime.strptime("2021-01-01", "%Y-%m-%d"), datetime.today())
        :param fill_alpha: Alpha value to be used for the area plots. Set to 0 or less to disable area plots
                          (default=0.2)
        :param fontsize: Fontsize to be used for axes label, tickmarks, and titles. (default=16)
        :param basefilename: Base name of the file(s) where the plots should eb saved to. Set to None to
                         only show but not save the plots. Figures will be saved as both PDF and PNG.
                         (default=None)
        """
        plt.figure(figsize=figsize)
        # Compute the proper yrange for the given timerange
        ymins = []
        ymaxs = []
        # Plot all lines and areas and track the min/max values for the timerange
        for k, v in codecovs.items():
            timestamps, coverage, nocov = CodecovInfo.get_time_and_coverage(v)
            if fill_alpha > 0:
                plt.fill_between(timestamps, coverage, alpha=fill_alpha)
            plt.plot(timestamps, coverage, '--o', label=k)
            if plot_xlim:
                r = np.logical_and(timestamps >= plot_xlim[0], timestamps <= plot_xlim[1])
                ymins.append(coverage[r].min())
                ymaxs.append(coverage[r].max())
            else:
                ymins.append(coverage.min())
                ymaxs.append(coverage.max())
        # Set the xlim
        if plot_xlim is not None:
            plt.xlim(plot_xlim)
        # Compute the approbriate ylim for the xlim timerange
        plt.ylim(np.min(ymins)-1, np.max(ymaxs) + 1)
        # Update fontsizes, labels, and legend
        plt.yticks(fontsize=fontsize)
        plt.xticks(fontsize=fontsize, rotation=45)
        plt.ylabel("Coverage in %", fontsize=fontsize)
        plt.legend(fontsize=fontsize)
        plt.tight_layout()
        # save and display
        if basefilename is not None:
            plt.savefig(basefilename + '.pdf', dpi=300)
            plt.savefig(basefilename + '.png', dpi=300)
        plt.show()
