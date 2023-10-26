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
from typing import Union
import subprocess
from io import StringIO


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
                         are pandas.DataFrame objects and the keys are strings with the statistic type,
                         i.e., 'sizes', 'blank', 'codes', 'comment', 'nfiles'
    :ivar contributors: Pandas dataframe wit contributors to the various repos determined via
                        `git shortlog --summary --numbered --email`.

    """
    def __init__(self,
                 output_dir: str,
                 git_paths: dict = None):
        """
        :param output_dir: Path to the directory where outputs are being stored
        :param git_paths: Dict of strings with the keys being the name of the tool and the values being
                          the git URL, e.g,. 'https://github.com/NeurodataWithoutBorders/pynwb.git'.
        """
        self.git_paths = git_paths if git_paths is not None else {}
        self.output_dir = output_dir
        self.source_dir = os.path.join(output_dir, 'src')
        self.cache_file_cloc = os.path.join(self.output_dir, 'cloc_stats.yaml')
        self.cache_file_commits = os.path.join(self.output_dir, 'commit_stats.yaml')
        self.cache_git_paths = os.path.join(self.output_dir, 'git_paths.yaml')
        self.cache_contributors = os.path.join(self.output_dir, 'contributors.tsv')
        self.commit_stats = None
        self.cloc_stats = None
        self.contributors = None

    @staticmethod
    def from_nwb(
            cache_dir: str,
            cloc_path: str,
            start_date: datetime = None,
            end_date: datetime = None,
            read_cache: bool = True,
            write_cache: bool = True,
            clean_source_dir: bool = True
    ):
        """
        Convenience function to compute GitCodeStats statistics for all NWB git repositories
        defined by GitRepos.merge(NWBGitInfo.GIT_REPOS, NWBGitInfo.NWB1_GIT_REPOS)

        For HDMF and the NDX_Extension_Smithy code statistics before the start date of the
        repo are set to 0. HDMF was extracted from PyNWB and as such, while there is code
        history before the official date for HDMF that part is history of PyNWB and so
        we set those values to 0. Similarly, the NDX_Extension_Smithy also originated
        from another code.

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
        :param clean_source_dir: Bool indicating whether to remove self.source_dir when finished
                           computing the code stats. This argument only takes effect when
                           code statistics are computed (i.e., not when data is loaded from cache)

        :return: Tuple with the: 1) GitCodeStats object with all NWB code statistics and
                 2) dict with the results form GitCodeStats.compute_summary_stats
                 3) dict with language statistics computed via GitCodeStats.compute_language_stats
                 4) list of all languages used
                 5) dict with the release date and timeline statistics
        """
        from nwb_project_analytics.gitstats import NWBGitInfo, GitRepos

        # Load results from the file cache if available
        all_nwb_repos = GitRepos.merge(NWBGitInfo.GIT_REPOS, NWBGitInfo.NWB1_GIT_REPOS)
        if GitCodeStats.cached(cache_dir) and read_cache:
            git_code_stats = GitCodeStats.from_cache(cache_dir)
        else:
            # Compute git code statistics
            git_code_stats = GitCodeStats(
                output_dir=cache_dir,
                git_paths={k: v.github_path for k, v in all_nwb_repos.items()}
            )
            # Define --since parameter to avoid inclusion of contributors before a repo started (e.g., for forks)
            contributor_params = {k: ("--since " + v.startdate.isoformat()) if v.startdate is not None else None
                                  for k, v in all_nwb_repos.items()}
            git_code_stats.compute_code_stats(cloc_path=cloc_path,
                                              clean_source_dir=clean_source_dir,
                                              contributor_params=contributor_params)
            if write_cache:
                git_code_stats.write_to_cache()

        # Define our reference date range depending on whether we include NWB 1 in the plots or not
        date_range = pd.date_range(
            start=NWBGitInfo.NWB2_START_DATE if start_date is None else start_date,
            end=datetime.today() if end_date is None else end_date,
            freq="D")

        # Compute the aligned data statistics
        summary_stats = git_code_stats.compute_summary_stats(date_range=date_range)

        # compute the language statistics
        ignore_lang = ['SUM', 'header']
        languages_used_all = git_code_stats.get_languages_used(ignore_lang)
        per_repo_lang_stats = git_code_stats.compute_language_stats(ignore_lang)

        # Clean up code statistics for repos that have a start date
        for repo_key in git_code_stats.git_paths.keys():
            repo_startdate = all_nwb_repos[repo_key].startdate
            # If a startdate is specified then clean up the statistics by setting
            # values before the startdate to 0. This is the case, e.g., when a
            # repo was build from a forke from a previous code and we want to capture the
            # statistics for the new code (e.g., HDMF was derived from PyNWB or
            # NWB GUIDE built on SODA etc.)
            if repo_startdate is not None:
                # Set all LOC values prior to the given date to 0
                for k in summary_stats.keys():
                    summary_stats[k][repo_key][:repo_startdate] = 0
                # also update the per-language stats for the repo
                datemask = (per_repo_lang_stats[repo_key].index < repo_startdate)
                per_repo_lang_stats[repo_key].loc[datemask] = 0

        return git_code_stats, summary_stats, per_repo_lang_stats, languages_used_all

    def write_to_cache(self):
        """Save the stats to YAML"""
        print("Caching results...")  # noqa T001
        print("saving %s" % self.cache_file_cloc)  # noqa T001
        yaml_dumper = yaml.YAML(typ='safe', pure=True)
        with open(self.cache_file_cloc, 'w') as outfile:
            yaml_dumper.dump(self.cloc_stats, outfile)
        print("saving  %s" % self.cache_file_commits)  # noqa T001
        with open(self.cache_file_commits, 'w') as outfile:
            yaml_dumper.dump(self.commit_stats, outfile)
        print("saving %s" % self.cache_git_paths)  # noqa T001
        with open(self.cache_git_paths, 'w') as outfile:
            yaml_dumper.dump(self.git_paths, outfile)
        print("saving %s" %  self.cache_contributors)  # noqa T001
        self.contributors.to_csv(self.cache_contributors , sep="\t", index=False)

    @staticmethod
    def from_cache(output_dir):
        """
        Create a GitCodeStats object from cached results
        :param output_dir: The output directory where the cache files are stored
        :return: A new GitCodeStats object with the resutls loaded from the cache
        """
        re = GitCodeStats(output_dir)
        yaml_safe_loader = yaml.YAML(typ='safe', pure=True)
        if GitCodeStats.cached(output_dir):
            print("Loading cached results: %s" % re.cache_file_cloc)  # noqa T001
            with open(re.cache_file_cloc) as f:
                re.cloc_stats = yaml_safe_loader.load(f)
            print("Loading cached results: %s" % re.cache_file_commits)  # noqa T001
            with open(re.cache_file_commits) as f:
                re.commit_stats = yaml_safe_loader.load(f)
            print("Loading cached results: %s" % re.cache_git_paths)  # noqa T001
            with open(re.cache_git_paths) as f:
                re.git_paths = yaml_safe_loader.load(f)
            print("Loading cached results: %s" % re.cache_contributors)  # noqa T001
            re.contributors = pd.read_csv(re.cache_contributors, header=[0,], sep="\t")
            return re
        raise ValueError("No cache available at %s" % output_dir)

    @staticmethod
    def cached(output_dir):
        """Check if a complete cached version of this class exists at output_dir"""
        temp = GitCodeStats(output_dir)
        return (os.path.exists(temp.cache_file_cloc) and
                os.path.exists(temp.cache_file_commits) and
                os.path.exists(temp.cache_git_paths) and
                os.path.exists(temp.cache_contributors))

    def compute_code_stats(
         self,
         cloc_path: str,
         clean_source_dir: bool = False,
         contributor_params: dict = None
    ):
        """
        Compute code statistics suing CLOC.

        NOTE: Repos will be checked out from GitHub and CLOC computed for all
              commits, i.e., the repo will be checked out at all commits of the
              repo and CLOC will be run. This process can be very expensive.
              Using the cache is recommended when possible.

        WARNING: This function calls self.clean_outdirs. Any previously cached results will be lost!

        :param cloc_path: Path to the cloc command for running cloc stats
        :param clean_source_dir: Bool indicating whether to remove self.source_dir when finished
        :param contributor_params: dict of string indicating additional command line parameters to pass to
                                  `git shortlog`. E.g., `--since="3 years"`. Similarly we may
                                  specify --since, --after, --before and --until.
        :return: None. The function initializes self.commit_stats, self.cloc_stats, and self.contributors
        """
        # Clean and create output directory
        self.clean_outdirs(output_dir=self.output_dir,
                           source_dir=self.source_dir)
        # Clone all repos
        print("Cloning all repos...")  # noqa T001
        git_repos = self.clone_repos(repos=self.git_paths, source_dir=self.source_dir)
        #git_repos = {k: git.Repo(os.path.join(self.source_dir, k)) for k, v in self.git_paths.items()}

        # Compute list of contributors for all the repos
        # We must do this first after cloning the repos since computing cloc checks out the repo in different states
        print("Compute contributors...")
        # TODO Use contributor_params here!!!
        print({name: os.path.basename(repo.working_tree_dir.split("/")[-1]) for name, repo in git_repos.items()})
        print({name: contributor_params.get(os.path.basename(repo.working_tree_dir.split("/")[-1]), None) for name, repo in git_repos.items()})
        print(contributor_params)
        repo_contributors = {
            name: GitCodeStats.get_contributors(
                repo=repo,
                contributor_params=contributor_params.get(os.path.basename(repo.working_tree_dir.split("/")[-1]), None))
            for name, repo in git_repos.items()}
        self.contributors = GitCodeStats.merge_contributors(data_frames=repo_contributors)

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
        print("Clean code source dir %s ..." % self.source_dir)
        if clean_source_dir:
            if os.path.exists(self.source_dir):
                shutil.rmtree(self.source_dir)

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

    def compute_language_stats(self,
                               ignore_lang=None):
        """
        Compute for each code the breakdown in lines-of-code per language (including
        blank, comment, and code lines for each language).

        The index of the resulting dataframe will typically be different for each code
        as changes occurred on different dates. The index reflects dates on which
        code changes occurred.

        :param ignore_lang: List of languages to ignore. Usually ['SUM', 'header'] are useful to ignore.

        :return: Dictionary of pandas.DataFrame objects with the language stats for the different repos
        """

        ignore_lang = [] if ignore_lang is None else ignore_lang
        per_repo_lang_stats = {}
        for codename, cloc_values in self.cloc_stats.items():
            # languages used in the current repo
            languages_used = np.unique([lang for cl in cloc_values
                                        for lang in cl['cloc'].keys()
                                        if lang not in ignore_lang])
            # dates available in the repo
            available_dates = pd.pandas.DatetimeIndex([cloc_entry['date']
                                                       for cloc_entry in cloc_values])
            curr_stats = {lang: [] for lang in languages_used}
            for cloc_entry in cloc_values:
                for lang in languages_used:
                    val = (cloc_entry['cloc'][lang]
                           if lang in cloc_entry['cloc']
                           else {'blank': 0, 'code': 0, 'comment': 0})
                    curr_stats[lang].append(val['blank'] + val['code'] + val['comment'])
            per_repo_lang_stats[codename] = pd.DataFrame.from_dict(curr_stats)
            per_repo_lang_stats[codename].index = available_dates

        return per_repo_lang_stats

    def get_languages_used(self, ignore_lang=None):
        """
        Get the list of languages used in the repos

        :param ignore_lang: List of strings with the languages that should be ignored. (Default=None)

        :return: array of strings with the unique set of languages used
        """
        if ignore_lang is None:
            ignore_lang = []
        return np.unique([lang for v in self.cloc_stats.values()
                          for cl in v for lang in cl['cloc'].keys() if lang not in ignore_lang])

    @staticmethod
    def clean_outdirs(output_dir, source_dir):
        """
        Delete the output directory and all its contents and create a new clean directory. Create a new source_dir.

        :param output_dir: Output directory for caching results
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
        try:
            os.system(command)
            yaml_safe_loader = yaml.YAML(typ='safe', pure=True)
            with open(out_file) as f:
                res = yaml_safe_loader.load(f)
        except:  # FileNotFoundError:
            res = None
        return res

    @staticmethod
    def git_repo_stats(repo: git.repo.base.Repo,
                       cloc_path: str,
                       output_dir: str):
        """
        Compute cloc statistics for the given repo.

        Run cloc only for the last commit on each day to avoid excessive runs

        :param repo: The git repository to process
        :param cloc_path: Path to run cloc on the command line
        :param output_dir: Path to the directory where outputs are being stored

        :returns: The function returns 2 elements, commit_stats and cloc_stats.
                  commit_stats is a list of dicts with information about all commits.
                  The list is sorted in time from most current [0] to oldest [-1].
                  cloc_stats is a list of dicts with CLOC code statistics. CLOC is
                  run only on the last commit on each day to reduce
                  the number of codecov runs and speed-up computation.
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
                if os.path.exists(cloc_yaml):
                    os.remove(cloc_yaml)  # Remove the yaml file, we don't need it
                if cloc_res['cloc'] is not None:
                    re_cloc_stats.append(cloc_res)
            # drop the commit from the dict to make sure we can save things in YAML
            commit.pop('commit', None)
        return re_commit_stats, re_cloc_stats


    @staticmethod
    def get_contributors(repo: Union[git.repo.base.Repo, str],
                         contributor_params: str = None):
        """
        Compute list of contributors for the given repo using  `git shortlog --summary --numbered --email`

        :param repo: The git repository to process
        :param contributor_params: String indicating additional command line parameters to pass to
                                  `git shortlog`. E.g., `--since="3 years"`. Similarly we may
                                  specify --since, --after, --before and --until.

        :return Pandas dataframe with the name, email, and number of contributions to the repo
        """
        src_dir = repo if isinstance(repo, str) else repo.working_dir
        cli_command = "git shortlog --summary --numbered --email"
        if contributor_params is not None:
            cli_command += " " + contributor_params
        print("Get contributors ... " + src_dir + "   " + cli_command)
        result = subprocess.run(
            [cli_command, ""],
            capture_output=True,
            text=True,
            cwd=src_dir,
            shell=True)
        print("result.stdout", result.stdout)
        print("result.stderr", result.stderr)
        result_text = result.stdout
        result_text = result_text.replace("<", "\t").replace(">", "")
        # parse the result
        result_text_io = StringIO(result_text)
        result_df = pd.read_csv(result_text_io,
                                sep="\t",
                                header=None,
                                names=["commits", "name", "email"])
        # remove trailing whitespaces from names
        result_df["name"] = [n.rstrip(" ") for n in result_df["name"]]
        print(result_df[["name", "email", "commits"]])
        return result_df[["name", "email", "commits"]]

    @staticmethod
    def merge_contributors(data_frames:dict,
                           merge_duplicates: bool = True):
        """
        Take dict of dataframes generated by `GitCodeStats.get_contributors` and merge them into a single dataframe

        :param data_frames: Dict of dataframes where the keys are the names of repos
        :param merge_duplicates: Attempt to detect and merge duplicate contributors by name and email
        :return: Combined pandas dataframe
        """
        print("Merging contributors ...")
        result = None
        for repo_name, df in data_frames.items():
            df = df.rename(columns={"name": "name", "email": "email", "commits": repo_name})
            if result is None:
                result = df
            else:
                result = result.merge(df,
                                      how='outer',
                                      on=['name', 'email'])
        # pd.merge turns the columns for the commits to floats and add NaN values
        # Replace the NaN values with 0 and turn the columns with commit counts back to int
        result = result.fillna(0).astype({repo_name: int for repo_name in data_frames.keys()})
        # result.columns = pd.MultiIndex.from_tuples(
        #     [('Contributor', 'name'), ('Contributor', 'email')] +
        #     [('Number of Commits', repo_name) for repo_name in data_frames.keys()])
        print("Merged:")
        print(result)
        if merge_duplicates:
            # Merge contributors with the same name
            grouped = result.groupby(["email"])  # merge with same email
            filtered = grouped.sum()  # Add up the contributions
            names = grouped.agg({"name": tuple})  # keep all names
            filtered["name"] = names
            filtered.reset_index(inplace=True)
            print("Depublicate by email:")
            print(filtered)
            # Merge contributors with the same email
            # If someone has both multiple emails and names then simply grouping by email name won't work
            # because we may already have multiple names at this point. Because of this we here compute
            # new column group_col where we compare all names of a row against all names of previous rows
            # and asign the index of the row that matched to then group by that column to merge name duplicates
            group_col = []
            for index, row in filtered.iterrows():
                names = row["name"]
                match = -1
                for index2, row2 in filtered.iterrows():
                    if index2 >= index or match >= 0:
                        break
                    names2 = row2["name"]
                    for n in names:
                        if np.any(np.array(names2) == n):
                            match = index2
                group_col.append(index if match < 0 else match)
            filtered['name_index'] = group_col
            grouped = filtered.groupby(["name_index"]) # group to find rows with matching names
            filtered = grouped.sum()   # sum up contributions
            filtered["email"] = grouped.agg({"email": tuple})
            filtered.reset_index(inplace=True, drop=True)  # remove the `name_index` column we added for grouping
            print("Depublicate by name:")
            print(filtered)
            # Remove duplicate emails and names
            filtered["name"] = [tuple(set(names)) for names in filtered["name"]]
            filtered["email"] = [tuple(set(emails)) for emails in filtered["email"]]
            print("Remove duplicate names and emails")
            print(filtered)
            # Update the final result
            result = filtered

        return result
