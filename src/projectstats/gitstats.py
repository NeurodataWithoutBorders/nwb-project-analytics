from datetime import datetime
from typing import NamedTuple
import numpy as np
import requests
from matplotlib import pyplot as plt
import matplotlib.dates as mdates
from collections import OrderedDict


class GitRepo(NamedTuple):
    """Named tuple with basic information about a GitHub repository"""

    owner: str
    """Owner of the repo on GitHub"""

    repo: str
    """Name of the repository"""

    @property
    def github_path(self):
        return "https://github.com/%s/%s.git" % (self.owner, self.repo)

class GitRepos(OrderedDict):
    """Dict where the keys are names of codes and the values are GitRepo objects"""
    def __init__(self,*arg,**kw):
        super().__init__(*arg, **kw)

    def get_info_objects(self):
        """Get an OrderedDict of GitHubRepoInfo object from the repos"""
        return OrderedDict([(k, GitHubRepoInfo(v)) for k, v in self.items()])

    @staticmethod
    def merge(o1, o2):
        """Merger two GitRepo dicts and return a new GitRepos dict with the combined items"""
        return GitRepos(list(o1.items()) + list(o2.items()))


class NWBGitInfo:
    """
    Class for storing basic information about NWB repositories
    """
    HDMF_START_DATE = "2019-03-13"
    """
    HDMF was originally part of PyNWB. As such code statistics before this start date for HDMF reflect stats
    that include both PyNWB and HDMF and will result in duplicate counting of code stats if PyNWB and HDMF
    are shown together. For HDMF 2019-03-13 coincides with the removal of HDMF from PyNWB with PR #850
    and the release of HDMF 1.0. For the plotting 2019-03-13 is therefore a good date to start considering HDMF
    stats to avoid duplication of code in statistics, even though the HDMF repo existed on GitHub already since
    2019-01-23T23:48:27Z, which could be alternatively considered as the start date. Older dates will include
    code history carried over from PyNWB to HDMF. Set to None to consider the full history of HMDF but as mentioned,
    this will lead to some duplicate counting of code before 2019-03-13
    """


    NWB1_DEPRECATION_DATE  = "2016-08-01"
    """
    Date when to declare the NWB 1.0 APIs as deprecated. The 3rd Hackathon was held on July 31 to August 1, 2017 at
    Janelia Farm, in Ashburn, Virginia, which marks the date when NWB 2.0 was officially accepted as the
    follow-up to NWB 1.0. NWB 1.0 as a project ended about 1 year before that.
    """

    NWB_EXTENSION_SMITHY_START_DATE = "2019-04-25"
    """
    NWB_Extension_Smithy is a fork with changes. We therefore should count only the sizes after the fork data
    which based on https://api.github.com/repos/nwb-extensions/nwb-extensions-smithy is 2019-04-25T20:56:02Z
    """

    GIT_REPOS = GitRepos(
        [("PyNWB", GitRepo(owner="NeurodataWithoutBorders", repo="pynwb")),
         ("MatNWB", GitRepo(owner="NeurodataWithoutBorders", repo="matnwb")),
         ("NWBWidgets", GitRepo(owner="NeurodataWithoutBorders", repo="nwb-jupyter-widgets")),
         ("NWBInspector", GitRepo(owner="NeurodataWithoutBorders", repo="nwbinspector")),
         ("Hackathons", GitRepo(owner="NeurodataWithoutBorders", repo="nwb_hackathons")),
         ("NWB_Schema", GitRepo(owner="NeurodataWithoutBorders", repo="nwb-schema")),
         ("NWB_Schema_Language", GitRepo(owner="NeurodataWithoutBorders", repo="nwb-schema-language")),
         ("HDMF", GitRepo(owner="hdmf-dev", repo="hdmf")),
         ("HDMF_Common_Schema", GitRepo(owner="hdmf-dev", repo="hdmf-common-schema")),
         ("HDMF_DocUtils", GitRepo(owner="hdmf-dev", repo="hdmf-docutils")),
         # "HDMF Schema Language" , https,//github.com/hdmf-dev/hdmf-schema-language
         ("NDX_Template", GitRepo(owner="nwb-extensions", repo="ndx-template")),
         ("NDX_Staged_Extensions",  GitRepo(owner="nwb-extensions", repo="staged-extensions")),
         #"NDX Webservices", "https,//github.com/nwb-extensions/nwb-extensions-webservices.git",
         ("NDX_Catalog",  GitRepo(owner="nwb-extensions", repo="nwb-extensions.github.io")),
         ("NDX_Extension_Smithy",  GitRepo(owner="nwb-extensions", repo="nwb-extensions-smithy"))
         ])
    """
    Dictionary with main NWB git repositories. The values are GitRepo tuples with the owner and repo name.
    """

    NWB1_GIT_REPOS = GitRepos(
        [("NWB_1.x_Matlab", GitRepo(owner="NeurodataWithoutBorders", repo="api-matlab")),
         ("NWB_1.x_Python", GitRepo(owner="NeurodataWithoutBorders", repo="api-python.git"))
         ])
    """
    Dictionary with main NWB 1.x git repositories. The values are GitRepo tuples with the owner and repo name.
    """


class GitHubRepoInfo:
    """
    Helper class to get information about a repo from GitHub

    :ivar repo: a GitRepo tuple with the owner and name of the repo
    """
    def __init__(self, repo):
        """
        :param repo: GitRepo tuple with the owner and name of the repo
        """
        self.repo = repo
        self.__releases = None

    def get_releases(self, use_cache=True):
        """
        Get the last 100 release for the given repo

        NOTE: GitHub uses pageination. Here we set the number of items per page to 100
               which should usually fit all releases, but in the future we may need to
               iterate over pages to get all the releases not just the latests 100

        :param use_cache: If set to True then return the chached results if computed previously.
                          In this case the per_page parameter will be ignored

        :raises: Error if response is not Ok, e.g., if the GitHub request limit is exceeded.
        :returns: List of dicts with the release data
        """
        # Return cached results if available
        if use_cache and self.__releases is not None:
            return self.__releases
        # Get restuls from GitGub
        per_page=100
        r = requests.get("https://api.github.com/repos/%s/%s/releases?per_page=%s" %
                         (self.repo.owner, self.repo.repo, str(per_page)))
        if not r.ok:
            r.raise_for_status()
        # cache the results
        if self.__releases is None:
            self.__releases = r.json()
        # return the results
        return self.__releases

    def get_release_names_and_dats(self, **kwargs):
        """
        Get names and dates of releases
        :param kwargs: Additional keyword arguments to be passed to self.get_releases

        :return: Tuple with the list of names as strings and the list of dates as datetime objects
        """
        releases = self.get_releases(**kwargs)
        names = []
        dates = []
        for rel in releases:
            if "Latest" not in rel["name"]:
                names.append(rel["tag_name"])
                dates.append(rel["published_at"])
        dates = [datetime.strptime(d[0:10], "%Y-%m-%d") for d in dates]
        return names, dates

    def plot_release_timeline(self, figsize=None, fontsize=14, month_intervals=3, xlim=None, ax=None, title_on_yaxis=False):
        """
        Plot a timeline of the releases for the repo

        Based on https://matplotlib.org/stable/gallery/lines_bars_and_markers/timeline.html

        :param figsize: Tuple with the figure size if a new figure is to be created, i.e., if ax is None
        :param fontsize: Fontsize to use for lables (default=14)
        :param month_intervals: Integer indicating the step size in number of month for the y  axis
        :param xlim: Optional tuple of datetime objects with the start and end-date for the x axis
        :param ax: Matplotlib axis object to be used for plotting
        :param title_on_yaxis: Show plot title as name of the y-axis (True) or as the main title (False) (default=False)

        :return: Matplotlib axis object use for plotting
        """
        names, dates = self.get_release_names_and_dats()


        # Choose some nice levels
        levels = np.tile([-5, 5, -3, 3, -1, 1],
                         int(np.ceil(len(dates)/6)))[:len(dates)]

        # Create figure and plot a stem plot with the date
        if ax is None:
            fig, ax = plt.subplots(figsize=(12,5) if figsize is None else figsize)

        ax.vlines(dates, 0, levels, color="dodgerblue")  # The vertical stems.
        ax.plot(dates, np.zeros_like(dates), "-o",
                color="k", markerfacecolor="w")  # Baseline and markers on it.

        # annotate lines
        for d, l, r in zip(dates, levels, names):
            ax.annotate(r, xy=(d, l),
                        xytext=(fontsize+2, np.sign(l)*3), textcoords="offset points",
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
            ax.set_ylabel(self.repo.repo, fontsize=fontsize)
        else:
            ax.set_title("%s release dates" % self.repo.repo, fontdict={"fontsize": fontsize})
            ax.yaxis.set_visible(False)

        ax.margins(y=0.1)
        return ax