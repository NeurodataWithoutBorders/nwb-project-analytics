"""
Module for querying GitHub repos
"""
from datetime import datetime
from typing import NamedTuple
import numpy as np
import pandas as pd
import requests
from collections import OrderedDict
from distutils.version import LooseVersion


class IssueLabel(NamedTuple):
    """
    Named tuple describing a label for issues on a Git repository.
    """

    label: str
    """
    Label of the issue, usually consisting <type>: <level>. <type> indicates the general
    area the label is used for, e.g., to assign a category, priority, or topic to an issue.
    <level> then indicates importance or sub-category with the given <type>, e.g., critical, high, medium, low
    level as part of the priority type
    """

    description: str
    """Description of the lable"""

    color: str
    """
    Hex code of the color for the label
    """

    @property
    def type(self):
        """
        Get the type of the issue label indicating the general area the label is used for, e.g.,
        to assign a category, priority, or topic to an issue.

        :returns: str with the type or None in case the label does not have a category (i.e., if the label
                  does not contain a ':' to separate the type and level).
        """
        if ':' in self.label:
            return self.label.split(":")[0]
        return None

    @property
    def level(self):
        """
        Get the level of the issue, indicating the importance or sub-category of the label  within the given self.type,
        e.g., critical, high, medium, low level as part of the priority type.

        :returns: str with the level or None in case the label does not have a level (e.g.,  if the label
                  does not contain a ':' to separate the type and level.
        """
        if ':' in self.label:
            label_parts = self.label.split(":")
            if len(label_parts) > 1 and len(label_parts[1]) > 0:
                return label_parts[1]
        return None

    @property
    def rgb(self):
        """
        Color code converted to RGB

        :returns: Tuple of ints with (red, green, blue) color values
        """
        hexcol = self.color.lstrip("#")
        return tuple(int(hexcol[i:i+2], 16) for i in (0, 2, 4))


class IssueLabels(OrderedDict):
    """OrderedDict where the keys are names of issues labels and the values are IssueLabel objects"""
    def __init__(self, *arg, **kw):
        super().__init__(*arg, **kw)

    @staticmethod
    def merge(o1, o2):
        """Merger two IssueLabels dicts and return a new IssuesLabels dict with the combined items"""
        return IssueLabels(list(o1.items()) + list(o2.items()))

    def get_by_type(self, label_type):
        """Get a new IssueLabels dict with just the lables with the given category"""
        return IssueLabels([(key, label)
                            for key, label in self.items()
                            if label.type is not None and label.type == label_type])

    @property
    def types(self):
        """Get a list of all type strings used in labels (may include None)"""
        re = set([self[label].type for label in self.keys()])
        return list(re)

    @property
    def levels(self):
        """Get a list of all level strings used in labels (may include Node)"""
        re = set([self[label].level for label in self.keys()])
        return list(re)

    @property
    def colors(self):
        """Get a list of all color hex codes uses"""
        re = set([self[label].color for label in self.keys()])
        return list(re)

    @property
    def rgbs(self):
        """Get a list of all rgb color codes used"""
        re = set([self[label].rgb for label in self.keys()])
        return list(re)


class GitRepo(NamedTuple):
    """Named tuple with basic information about a GitHub repository"""

    owner: str
    """Owner of the repo on GitHub"""

    repo: str
    """Name of the repository"""

    mainbranch: str
    """The main branch of the repository"""

    docs: str = None
    """Online documentation for the software"""

    @property
    def github_path(self):
        return "https://github.com/%s/%s.git" % (self.owner, self.repo)

    def get_issues_as_dataframe(self, date_threshold, github_obj, tqdm=None):
        """
        Get a dataframe for all issues with comments later than the given data

        :param date_threshold: Datetime object with data of latest comment threshold
        :param github_obj: PyGitHub github.Github object to use for retrieving issues
        :param tqdm: Supply the tqdm progress bar class to use
        :return:
        """
        issue_attrs = ['id', 'number', 'user', 'created_at',
                       'closed_at', 'state', 'title', 'milestone', 'labels',
                       'pull_request', 'closed_by', 'assignees', 'url']
        custom_issue_attrs = ['user_login', 'response_time', 'time_to_response',
                              'time_to_response_f', 'is_enhancement', 'is_help_wanted']
        issues = github_obj.get_repo("%s/%s" % (self.owner, self.repo)).get_issues(since=date_threshold)
        curr_df = pd.DataFrame(columns=(issue_attrs + custom_issue_attrs))
        if tqdm is not None:
            vals = tqdm(issues, position=1, total=issues.totalCount, desc='%s issues' % self.repo)
        else:
            vals = issues
        for issue in vals:
            curr_row = {k: getattr(issue, k) for k in issue_attrs}
            curr_row['response_time'] = pd.NaT
            curr_row['user_login'] = curr_row['user'].login
            curr_row['is_enhancement'] = np.any([label.name == "enhancement" for label in curr_row['labels']])
            curr_row['is_help_wanted'] = np.any([label.name == "help wanted" for label in curr_row['labels']])
            if issue.comments:
                for comment in issue.get_comments():
                    if issue.user != comment.user:  # don't count it if the user commented on their own issue
                        if pd.isnull(curr_row['response_time']) or curr_row['response_time'] > comment.created_at:
                            curr_row['response_time'] = comment.created_at
            # if user closes their own issue, count it as resolved
            if issue.closed_by == issue.user and issue.closed_at is not None:
                curr_row['response_time'] = np.min([curr_row['response_time'], issue.closed_at])
            curr_row['time_to_response'] = pd.to_timedelta(curr_row['response_time'] - curr_row['created_at'])
            curr_row['time_to_response_f'] = curr_row['time_to_response'] / np.timedelta64(1, 'D')
            curr_df = curr_df.append(curr_row, ignore_index=True)
        curr_df.is_enhancement = curr_df.is_enhancement.astype('bool')
        curr_df.is_help_wanted = curr_df.is_help_wanted.astype('bool')
        return curr_df


class GitRepos(OrderedDict):
    """Dict where the keys are names of codes and the values are GitRepo objects"""
    def __init__(self, *arg, **kw):
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
    HDMF_START_DATE = datetime(2019, 3, 13)
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

    NWB1_DEPRECATION_DATE = datetime(2016, 8, 1)
    """
    Date when to declare the NWB 1.0 APIs as deprecated. The 3rd Hackathon was held on July 31 to August 1, 2017 at
    Janelia Farm, in Ashburn, Virginia, which marks the date when NWB 2.0 was officially accepted as the
    follow-up to NWB 1.0. NWB 1.0 as a project ended about 1 year before that.
    """

    NWB_EXTENSION_SMITHY_START_DATE = datetime(2019, 4, 25)
    """
    NWB_Extension_Smithy is a fork with changes. We therefore should count only the sizes after the fork data
    which based on https://api.github.com/repos/nwb-extensions/nwb-extensions-smithy is 2019-04-25T20:56:02Z
    """

    NWB2_START_DATE = datetime(2016, 8, 31)
    """
    Date of the first release of PyNWB on the NWB GitHub. While some initial work was ongoing before that
    date, this was the first public release of code related to NWB 2.x
    """

    NWB2_BETA_RELEASE = datetime(2017, 11, 11)
    """
    Date of the first official beta release of NWB 2 as part of SfN 2017
    """

    NWB2_FIRST_STABLE_RELEASE = datetime(2019, 1, 19)
    """
    Date of the first official stable release of NWB 2.0
    """

    MISSING_RELEASE_TAGS = {
        # Add 2.0 release for NWB schema using the same data as for PyNWB 1.0
        # Add 2.0beta release for NWB schema using the same data for PyNWB 0.2.0
        "NWB_Schema": [("2.0.0", NWB2_FIRST_STABLE_RELEASE),
                       ("2.0.0b", NWB2_BETA_RELEASE)],
        # Add first beta release for MatNWB using the same date as for PyNWB 0.2.0
        "MatNWB": [("0.1.0b", NWB2_BETA_RELEASE)]
    }
    """
    List of early releases that are missing a tag on GitHub
    """

    GIT_REPOS = GitRepos(
        [("PyNWB",
          GitRepo(owner="NeurodataWithoutBorders",
                  repo="pynwb",
                  mainbranch="dev",
                  docs="https://pynwb.readthedocs.io")),
         ("MatNWB",
          GitRepo(owner="NeurodataWithoutBorders",
                  repo="matnwb",
                  mainbranch='master',
                  docs="https://neurodatawithoutborders.github.io/matnwb/")),
         ("NWBWidgets",
          GitRepo(owner="NeurodataWithoutBorders",
                  repo="nwb-jupyter-widgets",
                  mainbranch='master',
                  docs=None)),
         ("NWBInspector",
          GitRepo(owner="NeurodataWithoutBorders",
                  repo="nwbinspector",
                  mainbranch="dev",
                  docs="https://nwbinspector.readthedocs.io")),
         ("Hackathons",
          GitRepo(owner="NeurodataWithoutBorders",
                  repo="nwb_hackathons",
                  mainbranch="main",
                  docs="https://neurodatawithoutborders.github.io/nwb_hackathons/")),
         ("NWB_Overview",
          GitRepo(owner="NeurodataWithoutBorders",
                  repo="nwb-overview",
                  mainbranch="main",
                  docs="https://nwb-overview.readthedocs.io")),
         ("NWB_Schema",
          GitRepo(owner="NeurodataWithoutBorders",
                  repo="nwb-schema",
                  mainbranch="dev",
                  docs="https://nwb-schema.readthedocs.io")),
         ("NWB_Schema_Language",
          GitRepo(owner="NeurodataWithoutBorders",
                  repo="nwb-schema-language",
                  mainbranch="main",
                  docs="https://schema-language.readthedocs.io")),
         ("HDMF",
          GitRepo(owner="hdmf-dev",
                  repo="hdmf",
                  mainbranch="dev",
                  docs="https://hdmf.readthedocs.io")),
         ("HDMF_Zarr",
          GitRepo(owner="hdmf-dev",
                  repo="hdmf-zarr",
                  mainbranch="dev",
                  docs="https://hdmf-zarr.readthedocs.io")),
         ("HDMF_Common_Schema",
          GitRepo(owner="hdmf-dev",
                  repo="hdmf-common-schema",
                  mainbranch="main",
                  docs="https://hdmf-common-schema.readthedocs.io")),
         ("HDMF_DocUtils",
          GitRepo(owner="hdmf-dev",
                  repo="hdmf-docutils",
                  mainbranch="main",
                  docs=None)),
         ("HDMF_Schema_Language",
          GitRepo(owner="hdmf-dev",
                  repo="hdmf-schema-language",
                  mainbranch="main",
                  docs="https://hdmf-schema-language.readthedocs.io/")),
         ("NDX_Template",
          GitRepo(owner="nwb-extensions",
                  repo="ndx-template",
                  mainbranch="main",
                  docs="https://github.com/nwb-extensions/ndx-template#getting-started")),
         ("NDX_Staged_Extensions",
          GitRepo(owner="nwb-extensions",
                  repo="staged-extensions",
                  mainbranch='master',
                  docs=None)),
         # "NDX Webservices", "https,//github.com/nwb-extensions/nwb-extensions-webservices.git",
         ("NDX_Catalog",
          GitRepo(owner="nwb-extensions",
                  repo="nwb-extensions.github.io",
                  mainbranch="main",
                  docs="https://nwb-extensions.github.io/")),
         ("NDX_Extension_Smithy",
          GitRepo(owner="nwb-extensions",
                  repo="nwb-extensions-smithy",
                  mainbranch='master',
                  docs=None)),
         ("NeuroConv",
          GitRepo(owner="catalystneuro",
                  repo="neuroconv",
                  mainbranch="main",
                  docs="https://neuroconv.readthedocs.io"))
         ])
    """
    Dictionary with main NWB git repositories. The values are GitRepo tuples with the owner and repo name.
    """

    NWB1_GIT_REPOS = GitRepos(
        [("NWB_1.x_Matlab",
          GitRepo(owner="NeurodataWithoutBorders",
                  repo="api-matlab",
                  mainbranch="dev")),
         ("NWB_1.x_Python",
          GitRepo(owner="NeurodataWithoutBorders",
                  repo="api-python",
                  mainbranch="dev"))
         ])
    """
    Dictionary with main NWB 1.x git repositories. The values are GitRepo tuples with the owner and repo name.
    """

    CORE_API_REPOS = GitRepos(
        [("PyNWB",
          GitRepo(owner="NeurodataWithoutBorders",
                  repo="pynwb",
                  mainbranch="dev",
                  docs="https://pynwb.readthedocs.io")),
         ("HDMF",
          GitRepo(owner="hdmf-dev",
                  repo="hdmf",
                  mainbranch="dev",
                  docs="https://hdmf.readthedocs.io")),
         ("MatNWB",
          GitRepo(owner="NeurodataWithoutBorders",
                  repo="matnwb",
                  mainbranch='master',
                  docs="https://neurodatawithoutborders.github.io/matnwb/")),
         ("NWB_Schema",
          GitRepo(owner="NeurodataWithoutBorders",
                  repo="nwb-schema",
                  mainbranch="dev",
                  docs="https://nwb-schema.readthedocs.io"))
         ])
    """
    Dictionary with the main NWB git repos related the user APIs.
    """

    CORE_DEVELOPERS = ['rly', 'bendichter', 'oruebel', 'ajtritt', 'ln-vidrio', 'mavaylon1']
    """
    List of names of the core developers of NWB overall. These are used, e.g., when analyzing issue stats as
    core developer issues should not count against user issues.
    """

    STANDARD_ISSUE_LABELS = IssueLabels(
        [("category: bug",
          IssueLabel(label="category: bug",
                     description="errors in the code or code behavior",
                     color="#ee0701")),
         ("category: enhancement",
          IssueLabel(label="category: enhancement",
                     description="improvements of code or code behavior",
                     color="#1D76DB")),
         ("category: proposal",
          IssueLabel(label="category: proposal",
                     description="discussion of proposed enhancements or new features",
                     color="#dddddd")),
         ("compatibility: breaking change",
          IssueLabel(label="compatibility: breaking change",
                     description="fixes or enhancements that will break schema or API compatibility",
                     color="#B24AD1")),
         ("help wanted: good first issue",
          IssueLabel(label="help wanted: good first issue",
                     description="request for community contributions that are good for new contributors",
                     color="#0E8A16")),
         ("help wanted: deep dive",
          IssueLabel(label="help wanted: deep dive",
                     description="request for community contributions that will involve many parts of the code base",
                     color="#0E8A16")),
         ("priority: critical",
          IssueLabel(label="priority: critical",
                     description="impacts proper operation or use of core function of NWB or the software",
                     color="#a0140c")),
         ("priority: high",
          IssueLabel(label="priority: high",
                     description="impacts proper operation or use of feature important to most users",
                     color="#D93F0B")),
         ("priority: medium",
          IssueLabel(label="priority: medium",
                     description="non-critical problem and/or affecting only a small set of NWB users",
                     color="#FBCA04")),
         ("priority: low",
          IssueLabel(label="priority: low",
                     description="alternative solution already working and/or relevant to only specific user(s)",
                     color="#FEF2C0")),
         ("priority: wontfix",
          IssueLabel(label="priority: wontfix",
                     description="will not be fixed due to low priority and/or conflict with other feature/priority",
                     color="#ffffff")),
         ("topic: docs",
          IssueLabel(label="topic: docs",
                     description="Issues related to documentation",
                     color="#D4C5F9")),
         ("topic: testing",
          IssueLabel(label="topic: testing",
                     description="Issues related to testing",
                     color="#D4C5F9"))
         ])


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
        per_page = 100
        r = requests.get("https://api.github.com/repos/%s/%s/releases?per_page=%s" %
                         (self.repo.owner, self.repo.repo, str(per_page)))
        if not r.ok:
            r.raise_for_status()
        # cache the results
        if self.__releases is None:
            self.__releases = r.json()
        # return the results
        return self.__releases

    def get_release_names_and_dates(self, **kwargs):
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
                names.append(rel["tag_name"].lstrip('v'))
                dates.append(rel["published_at"])
        dates = [datetime.strptime(d[0:10], "%Y-%m-%d") for d in dates]
        return names, dates

    @staticmethod
    def get_version_jump_from_tags(tags):
        """
        Assuming semantic versioning release tags get the version jumps from the tags

        :returns: OrderedDict
        """
        def compare_versions(v1, v2):
            if v2.version[0] > v1.version[0]:
                return "major"
            elif v2.version[1] > v1.version[1]:
                return "minor"
            else:
                return "patch"
        versions = sorted([LooseVersion(t) for t in tags])
        # The first version needs to be treated seprately since we don't have a version to compare to
        version_jumps = OrderedDict([(versions[0].vstring,
                                      'major' if versions[0].version[0] > 0 else 'minor')])
        # Compare current and previous version to determine version jumps
        version_jumps.update(OrderedDict([(versions[i].vstring,
                                           compare_versions(versions[i-1], versions[i]))
                                         for i in range(1, len(versions), 1)]))
        # return results
        return version_jumps
