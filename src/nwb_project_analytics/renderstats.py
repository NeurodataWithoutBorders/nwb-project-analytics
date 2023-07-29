"""
Module with routines for plotting code and git statistics
"""
import matplotlib as mpl
import pandas as pd
import numpy as np
import warnings
from datetime import datetime, timedelta
from pandas.plotting._matplotlib.core import MPLPlot
import pandas
from .gitstats import GitHubRepoInfo, NWBGitInfo
from .codecovstats import CodecovInfo

# TODO: Update once/if pandas adds support for stepped area plots.
#       Area plot in pandas does not support step style. This patches the area plot
#       to support post step style needed for plotting code statistics based on
#       the suggestion in the corresponding pandas issue ticket
#       https://github.com/pandas-dev/pandas/issues/29451#issuecomment-551331961


class PatchedMPLPlot(MPLPlot):
    def _plot(*args, **kwds):
        if "step" in kwds:
            kwds["drawstyle"] = "steps-" + kwds["step"]
            kwds.pop("step")
        return MPLPlot._plot(*args, **kwds)


pandas.plotting._matplotlib.core.MPLPlot = PatchedMPLPlot




class RenderCommitStats:
    """
    Helper class for rendering commit history for repos
    """
    COLOR_ADDITIONS = "darkgreen"
    COLOR_DELETIONS = "darkred"

    @staticmethod
    def plot_commit_additions_and_deletions(
            commits: pd.DataFrame,
            repo_name: str = None,
            xaxis_dates: bool = False,
            bar_width: float = 0.8,
            color_additions: str = COLOR_ADDITIONS,
            color_deletions: str = COLOR_DELETIONS,
            xticks_rotate: int = 90
    ):
        """
        Plot the number of additions and deletions for commits as a bar plot

        :param commits: Pandas DataFrame with the commits generated via GitRepo.get_commits_as_dataframe
        :param repo_name: Name of the Git repository
        :param xaxis_dates: Place bars by date (True) or equally spaced by order of commits (False)
        :param bar_width: Width of the bars. When plotting with xaxis_dates=True using a narrow bar width can help
                          avoid overlap between bars
        :param color_additions: Color to be used for additions
        :param color_deletions: Color to be used for deletions
        :param xticks_rotate: Degrees to rotate x axis labels
        :return: Tuple with the Matplotlib figure and axis used
        """
        fig = mpl.pyplot.figure(figsize=(12, 6))
        ax = mpl.pyplot.gca()
        if len(commits) == 0:
            return fig
        x = commits['date'][::-1].values if xaxis_dates else range(0, len(commits))
        total_additions = np.sum(commits['additions'].astype('int'))
        total_deletions = np.sum(commits['deletions'].astype('int'))
        mpl.pyplot.bar(
            x,
            commits['additions'][::-1].astype('int'),
            label='additions (total=%i)' % total_additions,
            width=bar_width,
            color=color_additions
        )
        mpl.pyplot.bar(
            x,
            -1 * commits['deletions'][::-1].astype('int'),
            label='deletions (total=%i)' % total_deletions,
            width=bar_width,
            color=color_deletions
        )
        # use str(d)[:10] here because github uses numpy.datetime64 not standard python datetime
        mpl.pyplot.xticks(x, [str(d)[:10] for d in commits['date'][::-1].values], rotation=xticks_rotate)
        if xaxis_dates:
            ax.xaxis_date()
        mpl.pyplot.title("%sLines of code changed per commit" % (repo_name + ": " if repo_name else ""))
        mpl.pyplot.ylabel("Lines of code")
        mpl.pyplot.xlabel("Date")
        mpl.pyplot.legend()
        return fig, ax

    @staticmethod
    def plot_commit_cumulative_additions_and_deletions(
            commits: pd.DataFrame,
            repo_name: str = None,
            color_additions=COLOR_ADDITIONS,
            color_deletions=COLOR_DELETIONS
    ):
        """
        Plot the cumulative number of additions and deletions for commits as a stacked area plot

        :param commits: Pandas DataFrame with the commits generated via GitRepo.get_commits_as_dataframe(
        :param repo_name: Name of the Git repository
        :param color_additions: Color to be used for additions
        :param color_deletions: Color to be used for deletions
        :return: Tuple with the Matplotlib figure and axis used
        """
        fig = mpl.pyplot.figure(figsize=(12, 6))
        ax = mpl.pyplot.gca()
        if len(commits) == 0:
            return fig
        total_additions = np.sum(commits['additions'].astype('int'))
        total_deletions = np.sum(commits['deletions'].astype('int'))
        mpl.pyplot.stackplot(
            commits['date'][::-1].values,
            np.cumsum(commits['additions']).values.astype('int'),
            labels=['additions (total=%i)' % total_additions, ],
            colors=[color_additions]
        )
        mpl.pyplot.stackplot(
            commits['date'][::-1].values,
            -1 * np.cumsum(commits['deletions']).values.astype('int'),
            labels=['deletions (total=%i)' % total_deletions, ],
            colors=[color_deletions]
        )
        mpl.pyplot.title("%sCumulative lines of code changed" % (repo_name + ": " if repo_name else ""))
        mpl.pyplot.ylabel("Lines of code")
        mpl.pyplot.xlabel("Date")
        mpl.pyplot.legend()
        return fig, ax

    @staticmethod
    def plot_commit_additions_and_deletions_summary(
            commits: dict,
            bar_width: float = 0.8,
            color_additions=COLOR_ADDITIONS,
            color_deletions=COLOR_DELETIONS,
            xticks_rotate: int = 45,
            start_date: datetime = None,
            end_date: datetime = None
    ):
        """
        Plot bar chart with total additions and deletions for a collection of repositories

        :param commits: Dict where the keys are the nwb_project_analytics.gitstats.GitRepo objects
                        (or the string name of the repo) and the values are pandas DataFrames with
                        the commits generated via GitRepo.get_commits_as_dataframe
        :param bar_width: Width of the bars
        :param color_additions: Color to be used for additions
        :param color_deletions: Color to be used for deletions
        :param xticks_rotate: Degrees to rotate x axis labels
        :param start_date: Optional start date to be rendered in the title
        :param end_date: Optional end data to be rendered in the title
        """
        # list of repo names. The keys in commits dict are either string or GitHub repo objects
        repos = [repo if isinstance(repo, str) else repo.repo for repo in commits.keys()]
        additions = np.array([np.sum(cdf['additions']) for repo, cdf in commits.items()])
        deletions = np.array([np.sum(cdf['deletions']) for repo, cdf in commits.items()])

        fig = mpl.pyplot.figure(figsize=(12, 6))
        ax = mpl.pyplot.gca()
        x = range(len(repos))
        mpl.pyplot.bar(
            x,
            additions,
            label='additions (total=%i)' % np.sum(additions),
            width=bar_width,
            color=color_additions
        )
        mpl.pyplot.bar(
            x,
            -1 * deletions,
            label='deletions (total=%i)' % (-1 * np.sum(deletions)),
            width=bar_width,
            color=color_deletions
        )
        mpl.pyplot.xticks(x, repos, rotation=xticks_rotate)
        title = "Lines of code changed per repository"
        if start_date is not None:
            start_str = start_date.strftime("%Y-%m-%d")
            end_str = end_date.strftime("%Y-%m-%d") if end_date else ""
            title += " (%s - %s)" % (start_str, end_str)
        mpl.pyplot.title(title)
        mpl.pyplot.ylabel("Lines of code")
        mpl.pyplot.xlabel("Repository")
        mpl.pyplot.legend()
        return fig, ax


class RenderReleaseTimeline:
    """
    Helper class for rendering GitHubRepoInfo release timeslines
    """

    @staticmethod
    def plot_release_timeline(
            repo_name: str,
            dates: list,
            versions: list,
            figsize: tuple = None,
            fontsize: int = 14,
            month_intervals: int = 3,
            xlim: tuple = None,
            ax=None,
            title_on_yaxis: bool = False,
            add_releases: list = None):
        """
        Plot a timeline of the releases for a single GitHubRepoInfo repo

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
        if add_releases is not None:
            for r in add_releases:
                versions.append(r[0])
                dates.append(r[1])

        # Choose some nice levels
        try:
            version_jumps = GitHubRepoInfo.get_version_jump_from_tags(versions)
            levels = []
            curr_major = 5
            curr_minor = 2
            curr_patch = -5
            for n in versions:
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
            fig, ax = mpl.pyplot.subplots(figsize=(12, 5) if figsize is None else figsize)

        ax.vlines(dates, 0, levels, color="dodgerblue")  # The vertical stems.
        ax.plot(dates, np.zeros_like(dates), "-o",
                color="k", markerfacecolor="w")  # Baseline and markers on it.

        # annotate lines
        for d, l, r in zip(dates, levels, versions):
            ax.annotate(r, xy=(d, l),
                        xytext=(fontsize + 2, np.sign(l) * 3), textcoords="offset points",
                        horizontalalignment="right",
                        verticalalignment="bottom" if l > 0 else "top",
                        fontsize=fontsize)

        # format xaxis with 4 month intervals
        if xlim is not None:
            ax.set_xlim(xlim)
        ax.xaxis.set_major_locator(mpl.dates.MonthLocator(interval=month_intervals))
        ax.xaxis.set_major_formatter(mpl.dates.DateFormatter("%b %Y"))
        mpl.pyplot.setp(ax.get_xticklabels(), rotation=30, ha="right", fontsize=fontsize)

        # set the title
        if title_on_yaxis:
            ax.get_yaxis().set_ticks([])
            ax.set_ylabel(repo_name, fontsize=fontsize)
        else:
            ax.set_title("Release: %s" % repo_name, fontdict={"fontsize": fontsize})
            ax.yaxis.set_visible(False)

        # Set margins and grid lines
        ax.margins(y=0.1)

        # If levels of lines correspond to version jumps, then color code the background and add a legend
        if levels_by_version_jumps:
            # Create a Rectangle patch
            legend_items = []
            # Major releases background
            legend_items.append(mpl.patches.Rectangle(
                xy=(ax.get_xlim()[0], 3.5),  # xy origin
                width=ax.get_xlim()[1] - ax.get_xlim()[0],  # width
                height=ax.get_ylim()[1] - 3.5,
                linewidth=0,
                facecolor='lightgreen', edgecolor=None))
            # Minor releases background
            legend_items.append(mpl.patches.Rectangle(
                xy=(ax.get_xlim()[0], 0),  # xy origin
                width=ax.get_xlim()[1] - ax.get_xlim()[0],  # width
                height=3.5,
                linewidth=0,
                facecolor='lightblue', edgecolor=None))
            # Patch releases background
            legend_items.append(mpl.patches.Rectangle(
                xy=(ax.get_xlim()[0], ax.get_ylim()[0]),  # xy origin
                width=ax.get_xlim()[1] - ax.get_xlim()[0],  # width
                height=abs(ax.get_ylim()[0]),
                linewidth=0,
                facecolor='lightgray', edgecolor=None))
            # Add the mpl.patches to plot
            for patch in legend_items:
                ax.add_patch(patch)
            # Add the legend
            ax.legend(
                legend_items,
                ['Major', 'Minor', 'Patch'],
                loc='lower left',
                fontsize=fontsize,
                edgecolor='black',
                facecolor='white',
                title="Release Type",
                title_fontsize=fontsize,
                framealpha=1)
        ax.grid(axis="x", linestyle='dashed', color='gray')

        return ax

    @classmethod
    def plot_multiple_release_timeslines(
            cls,
            release_timelines: dict,
            add_releases: dict = None,
            date_range: tuple = None,
            month_intervals: int = 2,
            fontsize: int = 16,
            title: str = None
            ):
        """
        Plot multiple aligned timelines of the releases of a collection of GitHubRepoInfo repo objects

        :param release_timelines: Dict where the keys are the repo names and the values are tuples with the
                                  1) name of the versions and 2) dates of the versions
        :type github_repo_infos: OrderdDict (or dict) of GitHubRepoInfo objects
        :param add_releases: Sometimes libraries did not use git tags to mark releases. With this we can add
                            additional releases that are missing from the git tags. If None this is set to
                            NWBGitInfo.MISSING_RELEASE_TAGS by default. Set to empty dict if no additional
                            releases should be added.
        :type add_releases: Dict where the keys are a subset of the keys of the github_repos dict and the values are
                            lists of tuples with "name: str" and "date: datetime.strptime(d[0:10], "%Y-%m-%d")" of
                            additional releases for the given repo. Usually this is set
                            to NWBGitInfo.MISSING_RELEASE_TAGS
        :param date_range: Tuple of datetime objects with the start and stop time to use along the x axis
                           for rendering. If date_range is None it is automatically set to
                           (NWBGitInfo.NWB2_BETA_RELEASE - timedelta(days=60), datetime.today())
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
        fig, axes = mpl.pyplot.subplots(
            figsize=(16, len(release_timelines) * 4.2),
            nrows=len(release_timelines),
            ncols=1,
            sharex=True,
            sharey=False,
            squeeze=True)
        for i, repo in enumerate(release_timelines.keys()):
            versions, dates = release_timelines[repo]
            ax = cls.plot_release_timeline(
                repo_name=repo,
                versions=versions,
                dates=dates,
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
        mpl.pyplot.tight_layout()
        mpl.pyplot.subplots_adjust(wspace=0.0, hspace=0.02)

        return fig, axes


class RenderCodecovInfo:
    """
    Helper class for plotting CoedcovInfo data
    """

    @classmethod
    def __plot_single_codecov(
            cls,
            codename: str,
            timestamps,
            coverage,
            plot_xlim: tuple,
            fontsize: int,
            title: str = None
    ):
        """Internal helper function used to plot a single codecov  on an existing figure using pyplot"""
        mpl.pyplot.fill_between(timestamps, coverage)
        mpl.pyplot.plot(timestamps, coverage, '--o', color='black')
        if plot_xlim is not None:
            r = np.logical_and(timestamps >= plot_xlim[0], timestamps <= plot_xlim[1])
            mpl.pyplot.ylim(coverage[r].min()-1, coverage[r].max()+1)
            mpl.pyplot.xlim(plot_xlim)
        mpl.pyplot.ylabel("Coverage in %", fontsize=fontsize)
        if title is not None:
            mpl.pyplot.title(title, fontsize=fontsize)
        mpl.pyplot.yticks(fontsize=fontsize)
        mpl.pyplot.xticks(fontsize=fontsize, rotation=45)

    @classmethod
    def plot_codecov_individual(
            cls,
            codecovs: dict,
            plot_xlim: tuple = None,
            fontsize: int = 16,
            figsize: tuple = None,
            title: str = None
    ):
        """
        Plot coverage results for a code as an individual figure

        Example for setting for ``codecovs``:

        .. code:: Python

            codecovs = {r: CodecovInfo.get_pulls_or_commits(NWBGitInfo.GIT_REPOS[r],
                                                            key='commits', state='all',
                                                            branch=NWBGitInfo.GIT_REPOS[r].mainbranch)
                       for r in ['HDMF', 'PyNWB', 'MatNWB']}

        :param codecovs: Dictionary where the key is the name of the codes and the values are the output from
                         CodecovInfo.get_pulls_or_commits defining the coverage timeline for each code.
        :param plot_xlim: Tuple of datatime objects defining the time-range of the x-axis. E.g.,
                          plot_xlim=(datetime.strptime("2021-01-01", "%Y-%m-%d"), datetime.today())
        :param fontsize: Fontsize to be used for axes label, tickmarks, and titles. (default=16)
        :param figsize: Figure size tuple. Default is (18,6)
        :param title: Optional title for the figure

        :returns: Matplotlib figure
        """
        # Create separate figure for each code
        k = list(codecovs.keys())[0]
        v = codecovs[k]
        fig = mpl.pyplot.figure(figsize=figsize)
        timestamps, coverage, nocov = CodecovInfo.get_time_and_coverage(v)
        cls.__plot_single_codecov(k, timestamps, coverage, plot_xlim, fontsize)
        mpl.pyplot.tight_layout()
        return fig

    @classmethod
    def plot_codecov_grid(
            cls,
            codecovs: dict,
            plot_xlim: tuple = None,
            fontsize: int = 16,
            basefilename: str = None):
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
        fig, axes = mpl.pyplot.subplots(
            figsize=(8, len(codecovs)*4.2),
            nrows=len(codecovs), ncols=1,
            sharex=True, sharey=False,
            squeeze=True)
        i = 0
        for k, v in codecovs.items():
            timestamps, coverage, nocov = CodecovInfo.get_time_and_coverage(v)
            ax = axes[i] if len(codecovs) > 1 else axes
            mpl.pyplot.sca(ax)
            cls.__plot_single_codecov(k, timestamps, coverage, plot_xlim, fontsize)
            i += 1
        mpl.pyplot.tight_layout()
        if basefilename is not None:
            mpl.pyplot.savefig(basefilename + '.pdf', dpi=300)
            mpl.pyplot.savefig(basefilename + '.png', dpi=300)
        mpl.pyplot.show()

    @staticmethod
    def plot_codecov_multiline(
            codecovs: dict,
            plot_xlim: tuple = None,
            fill_alpha: float = 0.2,
            fontsize: int = 16,
            title: str = None,
            figsize: tuple = None):
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
        :param title: Optional title for the figure
        :param figsize: Opitonal tuple of ints with the figure size

        :returns: Matplotlib figure created here
        """
        fig = mpl.pyplot.figure(figsize=figsize)
        # Compute the proper yrange for the given timerange
        ymins = []
        ymaxs = []
        # Plot all lines and areas and track the min/max values for the timerange
        for k, v in codecovs.items():
            timestamps, coverage, nocov = CodecovInfo.get_time_and_coverage(v)
            if fill_alpha > 0:
                mpl.pyplot.fill_between(timestamps, coverage, alpha=fill_alpha)
            mpl.pyplot.plot(timestamps, coverage, '--o', label=k)
            if plot_xlim:
                r = np.logical_and(timestamps >= plot_xlim[0], timestamps <= plot_xlim[1])
                ymins.append(coverage[r].min())
                ymaxs.append(coverage[r].max())
            else:
                ymins.append(coverage.min())
                ymaxs.append(coverage.max())
        # Set the xlim
        if plot_xlim is not None:
            mpl.pyplot.xlim(plot_xlim)
        # Compute the approbriate ylim for the xlim timerange
        mpl.pyplot.ylim(np.min(ymins)-1, np.max(ymaxs) + 1)
        # Update fontsizes, labels, and legend
        mpl.pyplot.yticks(fontsize=fontsize)
        mpl.pyplot.xticks(fontsize=fontsize, rotation=45)
        mpl.pyplot.ylabel("Coverage in %", fontsize=fontsize)
        mpl.pyplot.legend(fontsize=fontsize)
        if title is not None:
            mpl.pyplot.title(title, fontsize=fontsize)
        mpl.pyplot.tight_layout()
        return fig


class RenderClocStats:
    """
    Helper class for rendering code line statistics generated
    using GitCodeStats, e.g., via GitCodeStats.from_nwb.
    """
    @staticmethod
    def plot_reposize_language(
            per_repo_lang_stats: dict,
            languages_used_all: list,
            repo_name: str,
            figsize: tuple = None,
            fontsize: int = 18,
            title: str = None
    ):
        """
        Plot repository size broken down by language for a particular repo

        To compute the language statistics for code repositories we can use

        .. code:: Python

            git_code_stats, summary_stats = GitCodeStats.from_nwb(...)
            ignore_lang = ['SUM', 'header']
            languages_used_all = git_code_stats.get_languages_used(ignore_lang)
            per_repo_lang_stats = git_code_stats.compute_language_stats(ignore_lang)

        :param per_repo_lang_stats: Dict with per repository language statistics compute via
                    GitCodeStats.compute_language_statistics
        :param  languages_used_all: List/array with the languages uses
        :param repo_name: Key in dataframes of summary_stats with the name of the code repository to plot.
        :param figsize: Figure size tuple. Default=(18, 10)
        :param fontsize: Fontsize
        :param title: Title of the plot
        :return: Matplotlib axis object used for plotting
        """
        # Create unique colors per language so we can be consistent across plots
        evenly_spaced_interval = np.linspace(0, 1, len(languages_used_all))
        language_colors = {languages_used_all[i]: mpl.cm.jet(x)  # tab20(x)
                           for i, x in enumerate(evenly_spaced_interval)}
        # Plot the per-language size statistics
        curr_df = per_repo_lang_stats[repo_name].copy()
        ax = curr_df.plot.area(
            figsize=(18, 10) if figsize is None else figsize,
            stacked=True,
            linewidth=2,
            fontsize=fontsize,
            step="post",
            # drawstyle="steps-post",  # this is waht it would be with just plot for line-plot
            color=[language_colors[lang] for lang in curr_df.columns]
        )
        # Adjust the labels
        mpl.pyplot.legend(loc=2, prop={'size': fontsize})
        mpl.pyplot.ylabel('Lines of Code (CLOC)', fontsize=fontsize)
        mpl.pyplot.grid(color='black', linestyle='--', linewidth=0.7, axis='both')
        if title is not None:
            mpl.pyplot.title(title, fontsize=fontsize)
        mpl.pyplot.tight_layout()
        # Place the legend next to plot
        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles[::-1],  # Reverse labels in the legend to match the stacking in the plot
                  labels[::-1],
                  title='Language',
                  loc='center left',
                  bbox_to_anchor=(1, 0.5),
                  fontsize=fontsize,
                  title_fontsize=fontsize)
        # Return the axis
        return ax

    @staticmethod
    def plot_reposize_code_comment_blank(
            summary_stats: dict,
            repo_name: str,
            title: str = None
    ):
        """
        Plot repository size broken down by code, comment, and blank for a particular repo

        :param summary_stats:  dict with the results form GitCodeStats.compute_summary_stats
        :param repo_name: Key in dataframes of summary_stats with the name of the code repository to plot.
        :param title: Title of the plot
        :return: Matplotlib axis object used for plotting
        """
        # Render all the plots
        curr_df = pd.DataFrame.from_dict({'code': summary_stats['codes'][repo_name],
                                          'blank': summary_stats['blanks'][repo_name],
                                          'comment': summary_stats['comments'][repo_name]})
        ax = curr_df.plot.area(
            figsize=(18, 10),
            stacked=True,
            linewidth=2,
            step='post',
            #  drawstyle="steps-post",  # This is what it would be for lineplot with plot instead of area
            fontsize=16)
        mpl.pyplot.legend(loc=2, prop={'size': 16})
        mpl.pyplot.ylabel('Lines of Code (CLOC)', fontsize=16)
        mpl.pyplot.grid(color='black', linestyle='--', linewidth=0.7, axis='both')
        if title is not None:
            mpl.pyplot.title(title, fontsize=20)
        mpl.pyplot.tight_layout()
        return ax

    @staticmethod
    def plot_cloc_sizes_stacked_area(
            summary_stats: dict,
            order: list = None,
            colors: list = None,
            title: str = None,
            fontsize: int = 20):
        """
        Stacked curve plot of code size statistics

        :param summary_stats:  dict with the results form GitCodeStats.compute_summary_stats
        :param order: List of strings selecting the order in which codes should be stacked in the plot.
                      If set to none then all keys in summary_stats will be used sorted alphabetically.
        :param colors: List of colors to be used. One per repo. Must be the same lenght as order.

        :return: Matplotlib axis object used for plotting
        """
        # define plot order
        if order is None:
            order = list(sorted(summary_stats['sizes'].keys()))
        # define plot colors
        if colors is None:
            # create colors from the jet color map
            evenly_spaced_interval = np.linspace(0, 1, len(order))
            colors = [mpl.cm.tab20(x) for x in evenly_spaced_interval]
            # mix up colors so that neighbouring areas have more dissimilar colors
            colors = ([c for i, c in enumerate(colors) if i % 2 == 0] +
                      [c for i, c in enumerate(colors) if i % 2 == 1])
        # plot the stacked curve plot
        ax = summary_stats['sizes'][order].plot.area(
            figsize=(18, 10),
            stacked=True,
            linewidth=1,
            fontsize=24,
            color=colors)
        # define the legend, axis labels, title etc.
        ax.get_yaxis().set_major_formatter(
            mpl.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))
        mpl.pyplot.legend(loc=2, prop={'size': fontsize})
        mpl.pyplot.ylabel('Lines of Code', fontsize=fontsize)
        mpl.pyplot.xlabel('Date', fontsize=fontsize)
        mpl.pyplot.grid(color='black', linestyle='--', linewidth=0.7, axis='both')
        # Place the legend next to plot
        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles[::-1],  # Reverse labels in the legend to match the stacking in the plot
                  labels[::-1],
                  title='Code Name',
                  loc='center left',
                  bbox_to_anchor=(1, 0.5),
                  title_fontsize=fontsize,
                  fontsize=fontsize-2)
        # set the tile
        if title is not None:
            mpl.pyplot.title(title, fontsize=fontsize)
        # mpl.pyplot.tight_layout()
        # return the plot axis
        return ax
