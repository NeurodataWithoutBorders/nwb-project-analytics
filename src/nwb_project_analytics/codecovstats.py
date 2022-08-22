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
        :param page_max: Integer with the maximum number of pages to request.
                         Set to None to indicate unlimited. (default=100)
        :param state: Filter list by state. One of all, open, closed, merged. Default: merged
        :param key: One of 'pulls' or 'commits'
        :param branch: Branch for which the stats should be retrieved. (Default=None)

        :returns: List of dicts (one per pull request) in order of appearance on the page
        """
        if key is None:
            key = 'pulls'
        if key not in ['pulls', 'commits']:
            raise ValueError("key must be in ['pulls', 'commits']")
        results = []
        page_index = 1
        page_max = 100
        while page_max is None or page_index < page_max:
            branch_str = '' if branch is None else 'branch/%s' % branch
            response = requests.get('https://codecov.io/api/gh/%s/%s/%s/%s?page=%i&state=%s' %
                                    (gitrepo.owner, gitrepo.repo, branch_str,  key, page_index, state))
            raw = response.json()
            if response.ok and len(raw[key]) > 0:
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
            """Internal helper function to retrieve the timestamp and coverage value"""
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
