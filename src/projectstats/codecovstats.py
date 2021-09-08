"""
Module for getting data from Codecov.io
"""
import numpy as np
import requests
import datetime
from matplotlib import pyplot as plt


class CodecovInfo:
    """Helper class for interacting with Codecov.io"""
    @staticmethod
    def get_pulls_or_commits(gitrepo, page_max=100, state='merged', key=None, branch=None):
        """
        Get all infos from pull request from Codecov.io

        :param gitrepo: GitRepo object with the owner and repo info
        :type gitrepo: GitRepo
        :param page_max: Integer with the maximum number of pages to request. Set to None to indicate unlimited. (default=100)
        'param state: Filter list by state. One of all, open, closed, merged. Default: merged
        :param key: One of 'pulls' or 'commits'
        :param branch: Branch for which the stats should be retrieved. (Default=None)

        :returns: List of dicts (one per pull request) in order of appearance on the page
        """
        if key is None:
            key = 'pulls'
        if not key in ['pulls', 'commits']:
            raise ValueError("key must be in ['pulls', 'commits']")
        results = []
        page_index = 1
        page_max = 100
        while page_max is None or page_index < page_max:
            branch_str = '' if branch is None else 'branch/%s' % branch
            response = requests.get('https://codecov.io/api/gh/%s/%s/%s/%s?page=%i&state=%s' % (gitrepo.owner, gitrepo.repo, branch_str,  key, page_index, state))
            raw = response.json()
            if len(raw[key]) > 0:
                results += raw[key]
            else:
                break
            page_index += 1
        return results

    @staticmethod
    def get_time_and_coverage(pulls_or_commits, filter_zeros=True):
        """
        Get the timestamps and total coverage information for all given pull requests.

        :param pulls: List of dicts (one per pull request usually generated via the CodecovInfo.get_pulls
        :param filter_zeros: Boolean indicating whether coverage values of 0 should be removed

        :returns: Tuple of three numpy arraus
                  1) Sorted array of datetime objects with the timestamps
                  2) Array of floats with the percent coverage data corresponding to the timestamps
                  3) Array of pulls missing coverage data
        """
        timestamps = []
        coverage = []
        no_coverage = []
        def get_stamp_and_cov(indict, filter_zeros):
            cov = float(indict['totals']['c'])
            if not (cov == 0 and filter_zeros):
                ts = indict['timestamp'] if 'timestamp' in indict else indict['updatestamp']
                # convert timestamps while ignoring microseconds
                stamp = datetime.datetime.strptime(ts[0:19], "%Y-%m-%dT%H:%M:%S" if 'T' in ts else "%Y-%m-%d %H:%M:%S")
                return (stamp, cov)
            return None, None

        for p in pulls_or_commits:
            ts, cov = None, None
            if 'totals' in p and p['totals'] is not None:
                ts, cov = get_stamp_and_cov(p, filter_zeros)
            elif 'head' in p and p['head'] is not None and 'totals' in p['head'] and p['head']['totals'] is not None:
                ts, cov = get_stamp_and_cov(p['head'], filter_zeros)
            elif 'base' in p and p['base'] is not None and 'totals' in p['base'] and p['base']['totals'] is not None:
                ts, cov = get_stamp_and_cov(p['base'], filter_zeros)
            if cov is not None:
                timestamps.append(ts)
                coverage.append(cov)
            else:
                no_coverage.append(p['pullid'])
        sortorder = np.argsort(timestamps)
        timestamps = np.array(timestamps)[sortorder]
        coverage = np.array(coverage)[sortorder]
        return timestamps, coverage, no_coverage

    @classmethod
    def __plot_single_codecov(cls, codename, timestamps, coverage, plot_xlim, fontsize):
        """Internal helper function used by  """
        plt.fill_between(timestamps, coverage)
        plt.plot(timestamps, coverage, '--o', color='black')
        if plot_xlim is not None:
            r = np.logical_and(timestamps >= plot_xlim[0] , timestamps <= plot_xlim[1])
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

        :param codecovs: Dictionary where the keys are the names of the codes and the values are the output from
                         CodecovInfo.get_pulls_or_commits defining the coverage timeline for each code. E.g., set to
                         >> {r: CodecovInfo.get_pulls_or_commits(NWBGitInfo.GIT_REPOS[r],
                                                              key='commits', state='all',
                                                              branch=NWBGitInfo.GIT_REPOS[r].mainbranch)
                            for r in ['HDMF', 'PyNWB', 'MatNWB']}
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

        :param codecovs: Dictionary where the keys are the names of the codes and the values are the output from
                         CodecovInfo.get_pulls_or_commits defining the coverage timeline for each code. E.g., set to
                         >> {r: CodecovInfo.get_pulls_or_commits(NWBGitInfo.GIT_REPOS[r],
                                                              key='commits', state='all',
                                                              branch=NWBGitInfo.GIT_REPOS[r].mainbranch)
                            for r in ['HDMF', 'PyNWB', 'MatNWB']}
        :param plot_xlim: Tuple of datatime objects defining the time-range of the x-axis. E.g.,
                          plot_xlim=(datetime.strptime("2021-01-01", "%Y-%m-%d"), datetime.today())
        :param fontsize: Fontsize to be used for axes label, tickmarks, and titles. (default=16)
        :param basefilename: Base name of the file(s) where the plots should eb saved to. Set to None to
                         only show but not save the plots. Figures will be saved as both PDF and PNG.
                         (default=None)
        """
        fig, axes = plt.subplots(figsize=(8, len(codecovs)*4.2),
                         nrows=len(codecovs),
                         ncols=1, sharex=True, sharey=False, squeeze=True)
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

        :param codecovs: Dictionary where the keys are the names of the codes and the values are the output from
                         CodecovInfo.get_pulls_or_commits defining the coverage timeline for each code. E.g., set to
                         >> {r: CodecovInfo.get_pulls_or_commits(NWBGitInfo.GIT_REPOS[r],
                                                              key='commits', state='all',
                                                              branch=NWBGitInfo.GIT_REPOS[r].mainbranch)
                            for r in ['HDMF', 'PyNWB', 'MatNWB']}
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
                r = np.logical_and(timestamps >= plot_xlim[0] , timestamps <= plot_xlim[1])
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
