"""
Module for computing code statistics using CLOC
"""
import os
import git
import ruamel.yaml as yaml
import time
import shutil
import pandas as pd
import numpy as np
from datetime import datetime


class GitCodeStats:
    """
    Class with functions to compute code statistics for repos stored on git

    The typical use is to

    >> git_code_stats = GitCodeStats(...)
    >> git_code_stats.compute_code_stats(...)
    >> git_code_stats.compute_summary_stats(...)

    If results have been computed previously and cached then do:

    >> git_code_stats = GitCodeStats.from_cache(...)
    >> git_code_stats.compute_summary_stats(...)

    We can check if valid cached files exists via GitCodeStats.cached() or the from_cache function will raise
    a ValueError if the cache does not exists.

    :ivar git_paths: Dict of strings with the keys being the name of the tool and the values being
                     the git URL, e.g,. 'https://github.com/NeurodataWithoutBorders/pynwb.git'.
    :ivar output_dir: Path to the directory where outputs are being stored
    :ivar source_dir: Path wheter the sources of repos are being checked out to. (self.output_dir/src)
    :ivar cache_file_cloc: Path to the YAML file for storing cloc statistics (may not exist if results are not cached)
    :ivar cache_file_commits: Path to the YAML file with the commit stats (may not exist if results are not cached)
    :ivar cloc_stats: Dict with the CLOC statistics
    :ivar commit_stats: Dict with the commit statistics.
    :ivar summary_stats: Dict with time-aligned summary statistics for all repos. The values of the dict
                         are pandas.DataFrame objects and the keys are:


    """
    def __init__(self, output_dir):
        """
        :param output_dir: Path to the directory where outputs are being stored
        """
        self.git_paths = {}
        self.output_dir = output_dir
        self.source_dir = os.path.join(output_dir, 'src')
        self.cache_file_cloc = os.path.join(self.output_dir, 'cloc_stats.yaml')
        self.cache_file_commits = os.path.join(self.output_dir, 'commit_stats.yaml')
        self.cache_git_paths = os.path.join(self.output_dir, 'git_paths.yaml')
        self.commit_stats = None
        self.cloc_stats = None

    @staticmethod
    def from_nwb(
            cache_dir: str,
            cloc_path: str,
            start_date: datetime = None,
            end_date: datetime = None,
            read_cache: bool = True,
            write_cache: bool = True):
        """
        Convenience function to compute GitCodeStats statistics for all NWB git repositories
        defined by GitRepos.merge(NWBGitInfo.GIT_REPOS, NWBGitInfo.NWB1_GIT_REPOS)

        :param cache_dir: Path to the director where the files with the cached results
                          are stored or should be written to
        :param cloc_path: Path to the cloc shell command
        :param start_date: Start date from which to compute summary statistics from.
                           If set to None, then use NWBGitInfo.NWB2_START_DATE
        :param end_date: End date until which to compute summary statistics to.
                           If set to None, then use datetime.today()
        :param read_cache: Bool indicating whether results should be loaded from cache
                           if cached files exists at cache_dir. NOTE: If read_cache is
                           True and files are in the cache then the results will be
                           loaded without checking results (e.g., whether results
                           in the cache are complete and up-to-date).
        :param write_cache: Bool indicating whether to write the results to the cache.

        :return: Tuple with the: 1) GitCodeStats object with all NWB code statistics and
                 2) dict with the results form GitCodeStats.compute_summary_stats
        """
        from nwb_project_analytics.gitstats import NWBGitInfo, GitRepos

        # Load results from the file cache if available
        if GitCodeStats.cached(cache_dir) and read_cache:
            git_code_stats = GitCodeStats.from_cache(cache_dir)
        else:
            git_paths = {k: v.github_path for k, v in
                         GitRepos.merge(NWBGitInfo.GIT_REPOS, NWBGitInfo.NWB1_GIT_REPOS).items()}
            git_code_stats = GitCodeStats(output_dir=cache_dir)
            git_code_stats.compute_code_stats(git_paths=git_paths,
                                              cloc_path=cloc_path,
                                              cache_results=write_cache)

        # Define our reference date range depending on whether we include NWB 1 in the plots or not
        date_range = pd.date_range(
            start=NWBGitInfo.NWB2_START_DATE if start_date is None else start_date,
            end=datetime.today() if end_date is None else end_date,
            freq="D")

        # Compute the aligned data statistics
        summary_stats = git_code_stats.compute_summary_stats(date_range=date_range)

        # Clean up HDMF summary statistic results results to mark start date of HDMF.
        # The HDMF repo was extracted from PyNWB. To avoid miscounting we'll set
        # all results before the start data for HDMF to 0
        # Set all LOC values prior to the given date to 0
        hdmf_start_date = NWBGitInfo.HDMF_START_DATE.strftime("%Y-%m-%d")
        for k in summary_stats.keys():
            summary_stats[k]['HDMF'][:hdmf_start_date] = 0

        # Clean up NDX_ExtensionSmithy results to mark start date for the extension smithy
        # Set all LOC values prior to the given data to 0
        extension_smithy_start_date = NWBGitInfo.NWB_EXTENSION_SMITHY_START_DATE.strftime("%Y-%m-%d")
        for k in summary_stats.keys():
            summary_stats[k]['NDX_Extension_Smithy'][:extension_smithy_start_date] = 0

        return git_code_stats, summary_stats

    @staticmethod
    def from_cache(output_dir):
        """
        Create a GitCodeStats object from cached results
        :param output_dir: The output directory where the cache files are stored
        :return: A new GitCodeStats object with the resutls loaded from the cache
        """
        re = GitCodeStats(output_dir)
        if GitCodeStats.cached(output_dir):
            print("Loading cached results: %s" % re.cache_file_cloc)  # noqa T001
            with open(re.cache_file_cloc) as f:
                re.cloc_stats = yaml.safe_load(f)
            print("Loading cached results: %s" % re.cache_file_commits)  # noqa T001
            with open(re.cache_file_commits) as f:
                re.commit_stats = yaml.safe_load(f)

            print("Loading cached results: %s" % re.cache_git_paths)  # noqa T001
            with open(re.cache_git_paths) as f:
                re.git_paths = yaml.safe_load(f)
            return re
        raise ValueError("No cache available at %s" % output_dir)

    @staticmethod
    def cached(output_dir):
        """Check if a cached version of this class exists at output_dir"""
        temp = GitCodeStats(output_dir)
        return (os.path.exists(temp.cache_file_cloc) and
                os.path.exists(temp.cache_file_commits) and
                os.path.exists(temp.cache_git_paths))

    def compute_code_stats(self, git_paths, cloc_path, cache_results=True):
        """
        Compute code statistics suing CLOC.

        NOTE: Repos will be checked out from GitHub and CLOC computed for all
              commits, i.e., the repo will be checked out at all commits of the
              repo and CLOC will be run. This process can be very expensive.
              Using the cache is recommended when possible.

        WARNING: This function calls self.clean_outdirs. Any previously cached results will be lost!


        :param git_paths: Dict of strings with the keys being the name of the tool and the values being
                          the git URL, e.g,. 'https://github.com/NeurodataWithoutBorders/pynwb.git'.
        :param cloc_path: Path to the cloc command for running cloc stats
        :param load_cached_results: Boolean indicating whether results should be loaded from cache if possible or
                                    if the cache should be cleaned and results recomputed. NOTE: Setting to false
                                    will lead to calling clean_outdir to clean up results.
        :type load_cached_results: bool
        :param cache_results: Cache results as YAML to self.outdir
        :type cache_results: bool
        :return: None. The function initializes self.commit_stats and self.cloc_stats
        """
        self.git_paths = git_paths
        # Clean and create output directory
        self.clean_outdirs(output_dir=self.output_dir,
                           source_dir=self.source_dir)
        # Clone all repos
        print("Cloning all repos...")  # noqa T001
        git_repos = self.clone_repos(repos=self.git_paths, source_dir=self.source_dir)
        # Compute CLOC and Commit statistics for all repos
        self.commit_stats = {}
        self.cloc_stats = {}
        for name, repo in git_repos.items():
            print("Compute CLOC stats: %s" % name)  # noqa T001
            commit_res, cloc_res = self.git_repo_stats(
                repo,
                cloc_path=cloc_path,
                output_dir=self.output_dir)
            self.commit_stats[name] = commit_res
            self.cloc_stats[name] = cloc_res
        # Cache the results if requested
        print("Caching results...")  # noqa T001
        if cache_results:
            print("saving %s" % self.cache_file_cloc)  # noqa T001
            with open(self.cache_file_cloc, 'w') as outfile:
                yaml.dump(self.cloc_stats, outfile)
            print("saving  %s" % self.cache_file_commits)  # noqa T001
            with open(self.cache_file_commits, 'w') as outfile:
                yaml.dump(self.commit_stats, outfile)
            print("saving %s" % self.cache_git_paths)  # noqa T001
            with open(self.cache_git_paths, 'w') as outfile:
                yaml.dump(self.git_paths, outfile)

    def compute_summary_stats(self, date_range):
        """
        Compile summary of line-of-code (LOC) across repos by categories: sizes, blanks, codes, comments, and nfiles

        The goal is to align and expand results from all repos so that we can plot them together.
        Here we create a continuous date range and expand the results from all repos to align with
        our common time axis. For dates where no new CLOC stats are recorded for a repo, the statistics
        from the previous time are carried forward to fill in the gaps.

        :param date_range: Pandas datarange object for which the stats should be computed
        :type date_range: pandas.date_range
        :return: Dict where the values are Pandas DataFrame objects with summary statistics
                 and the keys are strings with the statistic type, i.e., 'sizes', 'blank',
                 'codes', 'comment', 'nfiles'
        """
        if self.commit_stats is None or self.cloc_stats is None:
            raise AssertionError("commit_stats and cloc_stats have not been initalized. Call compute_code_stats first.")

        # Align and expand our results
        repo_sizes_aligned = {}
        repo_blanks_aligned = {}
        repo_codes_aligned = {}
        repo_comments_aligned = {}
        repo_nfiles_aligned = {}

        # Iterate through all repos and organize the size stats for the given date_range
        for k, v in self.cloc_stats.items():
            # Dates and CLOC size for the current repo
            curr_dates = pd.pandas.DatetimeIndex([cloc_entry['date'] for cloc_entry in v])[::-1]
            curr_sizes = [np.sum([v for k, v in cloc_entry['cloc']['SUM'].items() if k != 'nFiles'])
                          for cloc_entry in v][::-1]
            curr_blanks = [cloc_entry['cloc']['SUM']['blank'] for cloc_entry in v][::-1]
            curr_codes = [cloc_entry['cloc']['SUM']['code'] for cloc_entry in v][::-1]
            curr_comments = [cloc_entry['cloc']['SUM']['comment'] for cloc_entry in v][::-1]
            curr_nfiles = [cloc_entry['cloc']['SUM']['nFiles'] for cloc_entry in v][::-1]

            # Expand the data so we carry forward values for dates where the repo has not changed
            curr_index = 0
            curr_val_sizes = 0
            curr_val_blanks = 0
            curr_val_codes = 0
            curr_val_comments = 0
            curr_val_nfiles = 0
            expanded_sizes = []
            expanded_blanks = []
            expanded_codes = []
            expanded_comments = []
            expanded_nfiles = []
            # If our start date of the repo is before the start of our date_range,
            # then we need to search for the approbriate start values and index
            # as the repo has a valid state prior to the range we are looking at
            if date_range[0] > curr_dates[0]:
                if date_range[0] > curr_dates[-1]:
                    curr_index = len(curr_dates) - 1
                else:
                    for di, d in enumerate(curr_dates):
                        if d > date_range[0]:
                            curr_index = di - 1
                            break
                curr_val_sizes = curr_sizes[curr_index]
                curr_val_blanks = curr_blanks[curr_index]
                curr_val_codes = curr_codes[curr_index]
                curr_val_comments = curr_comments[curr_index]
                curr_val_nfiles = curr_nfiles[curr_index]

            # Compute all the sizes
            for d in date_range:
                # If we found a matching date, then update the results
                # Else we'll carry-forward the previous value since the
                # repo has not changed
                if d == curr_dates[curr_index]:
                    curr_val_sizes = curr_sizes[curr_index]
                    curr_val_blanks = curr_blanks[curr_index]
                    curr_val_codes = curr_codes[curr_index]
                    curr_val_comments = curr_comments[curr_index]
                    curr_val_nfiles = curr_nfiles[curr_index]
                    if curr_index < (len(curr_dates) - 1):
                        curr_index += 1
                # Append the approbriate value for the current data d
                expanded_sizes.append(curr_val_sizes)
                expanded_blanks.append(curr_val_blanks)
                expanded_codes.append(curr_val_codes)
                expanded_comments.append(curr_val_comments)
                expanded_nfiles.append(curr_val_nfiles)
            # Save the expanded results for the current repo k
            repo_sizes_aligned[k] = np.asarray(expanded_sizes)
            repo_blanks_aligned[k] = np.asarray(expanded_blanks)
            repo_codes_aligned[k] = np.asarray(expanded_codes)
            repo_comments_aligned[k] = np.asarray(expanded_comments)
            repo_nfiles_aligned[k] = np.asarray(expanded_nfiles)

        # Convert results to Pandas
        repo_sizes_aligned_df = pd.DataFrame.from_dict(repo_sizes_aligned)
        repo_sizes_aligned_df.index = date_range
        repo_blanks_aligned_df = pd.DataFrame.from_dict(repo_blanks_aligned)
        repo_blanks_aligned_df.index = date_range
        repo_codes_aligned_df = pd.DataFrame.from_dict(repo_codes_aligned)
        repo_codes_aligned_df.index = date_range
        repo_comments_aligned_df = pd.DataFrame.from_dict(repo_comments_aligned)
        repo_comments_aligned_df.index = date_range
        repo_nfiles_aligned_df = pd.DataFrame.from_dict(repo_codes_aligned)
        repo_nfiles_aligned_df.index = date_range

        return {'sizes': repo_sizes_aligned_df,
                'blanks': repo_blanks_aligned_df,
                'codes': repo_codes_aligned_df,
                'comments': repo_comments_aligned_df,
                'nfiles': repo_nfiles_aligned_df}

    def compute_language_stats(self, ignore_lang=None):
        """

        :param ignore_lang: List of languages to ignore. Usually ['SUM', 'header'] are useful to ignore.

        :return: Dictionary of pandas.DataFrame objects with the language stats for the different repos
        """

        ignore_lang = [] if ignore_lang is None else ignore_lang
        per_repo_lang_stats = {}
        for k, v in self.cloc_stats.items():
            # languages used in the current repo
            languages_used = np.unique([lang for cl in v for lang in cl['cloc'].keys() if lang not in ignore_lang])
            # linear range of dates across the lifetime of this repo
            date_range_used = pd.date_range(start=self.cloc_stats[k][-1]['date'],
                                            end=time.strftime("%d %b %Y", time.localtime()),
                                            freq="D")
            # start index in the CLOC data available for the repo
            curr_index = 0
            # current values to be used
            curr_values = {lang: 0 for lang in languages_used}
            # dates available in the repo
            curr_dates = pd.pandas.DatetimeIndex([cloc_entry['date'] for cloc_entry in v])[::-1]
            curr_stats = {lang: [] for lang in languages_used}
            # iterate through all date values and set the repo counts
            for d in date_range_used:
                # If we found a matching date, then update the results
                # Else we'll carry-forward the previous value since the
                # repo has not changed
                if d == curr_dates[curr_index]:
                    # Update the current values to report until we find curr_dates[curr_index+1]
                    for lang, val in v[curr_index]['cloc'].items():
                        if lang in curr_values:  # e.g., SUM is being ignored
                            curr_values[lang] = val['blank'] + val['code'] + val['code']
                    # Move to the next date in the repo
                    if curr_index < (len(curr_dates) - 1):
                        curr_index += 1
                # Copy the current values into our curr_stats dict
                for cl, cv in curr_values.items():
                    curr_stats[cl].append(cv)
            # Now that we have our stats lets convert them to pandas
            per_repo_lang_stats[k] = pd.DataFrame.from_dict(curr_stats)
            per_repo_lang_stats[k].index = date_range_used[::-1]

        return per_repo_lang_stats

    def get_languages_used(self, ignore_lang=None):
        """
        Get the list of languages used in the repos

        :param ignore_lang: List of strings with the languages that should be ignored. (Default=None)
        """
        if ignore_lang is None:
            ignore_lang = []
        return np.unique([lang for v in self.cloc_stats.values()
                          for cl in v for lang in cl['cloc'].keys() if lang not in ignore_lang])

    @staticmethod
    def clean_outdirs(output_dir, source_dir):
        """
        Delete the output directory and all its contents and create a new clean directory. Create a new source_dir.

        :param output_dir: Output directory for chaching results
        :param source_dir: Directory for storing repos checked out from git

        :returns: A tuple of two strings with the output_dir and source_dir for git sources
        """
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.mkdir(output_dir)
        os.mkdir(source_dir)
        return output_dir, source_dir

    @staticmethod
    def clone_repos(repos, source_dir):
        """
        Clone all of the given repositories.

        :param repos: Dict where the keys are the names of the repos and the
                      values are the git source path to clone
        :param source_dir: Directory where all the git repos should be cloned to.
                      Each repo will be cloned into a subdirectory in source_dir
                      that is named after the corresponding key in the repos dict.
        :returns: Dict where the keys are the same as in repos but the values
                  are instances of git.repo.base.Repo pointing to the corresponding
                  git repository.
        """
        git_repos = {}
        for k, v in repos.items():
            print("Cloning: %s" % k)  # noqa T001
            git_repos[k] = git.Repo.clone_from(v, os.path.join(source_dir, k))
        return git_repos

    @staticmethod
    def run_cloc(cloc_path, src_dir, out_file):
        """
        Run CLOC on the given srcdir, save the results to outdir, and return the parsed
        results.
        """
        command = "%s --yaml --report-file=%s %s" % (cloc_path, out_file, src_dir)
        os.system(command)
        with open(out_file) as f:
            res = yaml.safe_load(f)
        return res

    @staticmethod
    def git_repo_stats(repo, cloc_path, output_dir):
        """
        :param repo: The git repository to process
        :type repo: git.repo.base.Repo

        :returns: List of dicts with information about all commits. The list
                  is sorted in time from most current [0] to oldest [-1]
        """
        # Get hexsha and data of all commits
        re_commit_stats = []
        # Commits are sorted in time from newest to oldest
        for commit in repo.iter_commits():
            re_commit_stats.append(
                {'time': time.asctime(time.gmtime(commit.committed_date)),
                 'hexsha': commit.hexsha,
                 'author': commit.author.name,
                 'committer': commit.committer.name,
                 'summary': commit.summary,
                 'commit': commit})
        # iterate through all the commits in order and compute the cloc stats
        re_cloc_stats = []
        for commit in re_commit_stats:
            date = time.strftime("%d %b %Y", time.gmtime(commit['commit'].committed_date))
            # Run cloc only for the last commit on each day
            if len(re_cloc_stats) == 0 or date != re_cloc_stats[-1]['date']:
                cloc_res = {'hexsha': commit['hexsha'], 'date': date, 'time': commit['time']}
                repo.git.checkout(commit['hexsha'])
                cloc_yaml = os.path.join(
                    output_dir,
                    "%s.yaml" % os.path.basename(repo.working_dir))
                # "%s_%s.yaml" % (os.path.dirname(repo.working_dir), commit['hexsha']))
                cloc_res['cloc'] = GitCodeStats.run_cloc(
                    cloc_path=cloc_path,
                    src_dir=repo.working_dir,
                    out_file=cloc_yaml)
                os.remove(cloc_yaml)  # Remove the yaml file, we don't need it
                re_cloc_stats.append(cloc_res)
            # drop the commit from the dict to make sure we can save things in YAML
            commit.pop('commit', None)
        return re_commit_stats, re_cloc_stats