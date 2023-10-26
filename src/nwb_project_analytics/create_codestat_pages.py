"""Script for creating rst pages and figures with NWB code statistics"""
import os
import shutil
from datetime import datetime
from matplotlib import pyplot as plt
from collections import OrderedDict

from nwb_project_analytics.codestats import GitCodeStats
from nwb_project_analytics.gitstats import NWBGitInfo, GitRepo, GitHubRepoInfo
from nwb_project_analytics.codecovstats import CodecovInfo
from nwb_project_analytics.renderstats import (
    RenderClocStats,
    RenderReleaseTimeline,
    RenderCodecovInfo)
from hdmf_docutils.doctools.output import PrintHelper
from hdmf_docutils.doctools.rst import RSTDocument, RSTFigure, RSTToc


def init_codestat_pages_dir(out_dir):
    """
    Delete out_dir and all its contents and create a new clean out_dir
    :param out_dir: Directory to be removed
    :return:
    """
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    os.mkdir(out_dir)


def create_toolstat_page(
        out_dir: str,
        repo_name: str,
        repo: GitRepo,
        figures: OrderedDict,
        print_status: bool = True):
    """
    Create a page with the statistics for a particular tool

    :param out_dir: Directory where the RST file should be saved to
    :param repo_name: Name of the code repository
    :param figures: OrderedDict of RSTFigure object to render on the page
    :param print_status: Print status of creation (Default=True)
    :return:
    """
    tool_page_name = "%s_stats.rst" % repo_name
    if print_status:
        PrintHelper.print("CREATING: %s" % tool_page_name, PrintHelper.BOLD)
    tool_codestats_rst = RSTDocument()
    tool_codestats_rst.add_label("%s-tools-statistics" % repo_name)
    tool_codestats_rst.add_section("%s" % repo_name)
    if "loc" or "lang_loc" in figures:
        tool_codestats_rst.add_subsection("Lines of Code")
        tool_codestats_rst.add_figure(figure=figures.pop('loc', None))
        tool_codestats_rst.add_figure(figure=figures.pop('lang_loc', None))
    if "codecov" in figures:
        tool_codestats_rst.add_subsection("Test Coverage")
        tool_codestats_rst.add_figure(figure=figures.pop("codecov", None))
    if "releases" in figures:
        tool_codestats_rst.add_subsection("Release History")
        tool_codestats_rst.add_figure(figure=figures.pop('releases', None))
    if len(figures) > 0:
        tool_codestats_rst.add_subsection("Additional Figures:")
        for key, fig in figures.items():
            tool_codestats_rst.add_figure(figure=fig)
    # Compile the list of links
    tool_infolist = []
    tool_infolist.append("Source: %s  (main branch = ``%s``)" % (repo.github_path, repo.mainbranch))
    if repo.docs is not None:
        tool_infolist.append("Docs: %s" % repo.docs)
    if repo.logo is not None:
        tool_infolist.append("Logo: %s" % repo.logo)
    if len(tool_infolist) > 0:
        tool_codestats_rst.add_subsection("Additional Information")
        tool_codestats_rst.add_list(content=tool_infolist)
    # # Add badges
    # tool_codestats_rst.add_figure(RSTFigure(f"https://img.shields.io/github/issues-raw/{repo.owner}/{repo.repo}",
    #                                         target=repo.github_issues_url))
    # tool_codestats_rst.add_figure(RSTFigure(f"https://img.shields.io/github/issues-pr-raw/{repo.owner}/{repo.repo}",
    #                                         target=repo.github_pulls_url))

    # Write the file and return
    tool_codestats_rst.write(os.path.join(out_dir, tool_page_name))
    return tool_page_name


def __create_loc_summary_plot(
        summary_stats,
        code_order,
        out_dir: str,
        print_status: bool = True):
    """
    Internal helper function used to render the the summary plot of the lines of code of all repos

    :param summary_stats: Summary statistics from GitCodeStats.compute_summary_stats
    :param code_order: List of code names to sort entries in the plot
    :param out_dir: Output directory
    :param print_status: Print status of creation (Default=True)
    :return: RSTFigure to add to the document
    """
    if print_status:
        PrintHelper.print("PLOTTING: nwb_reposize_all", PrintHelper.BOLD)
    ax = RenderClocStats.plot_cloc_sizes_stacked_area(
        summary_stats=summary_stats,
        order=code_order,  # show all codes in alphabetical order
        colors=None,  # use default color
        title="NWB code repository sizes in lines-of-code (LOC)",
        fontsize=20)
    plt.savefig(os.path.join(out_dir, "nwb_reposize_all.pdf"))
    plt.savefig(os.path.join(out_dir, "nwb_reposize_all.png"), dpi=300)
    plt.close()
    del ax
    fig = RSTFigure(
        image_path="nwb_reposize_all.png",
        alt="NWB code repository sizes",
        width="100%")
    return fig


def __create_nwb_release_timeline_summary_plot(
        release_timelines: dict,
        out_dir: str,
        print_status: bool = True):
    """
    Internal helper function used to render the the summary plot of the release timeline

    :param release_timelines: Dict where the keys are the repo names and the values are tuples with the
           1) name of the versions and 2) dates of the versions
    :param out_dir: Output directory
    :param print_status: Print status of creation (Default=True)
    :return: RSTFigure to add to the document
    """
    if print_status:
        PrintHelper.print("PLOTTING: releases_timeline_nwb_main", PrintHelper.BOLD)
    # filter the release timelines to only select the main repos
    nwb_main_release_timelines = OrderedDict(
        [(k, release_timelines[k])
         for k in ['PyNWB', 'HDMF', 'MatNWB', 'NWB_Schema']]
    )
    RenderReleaseTimeline.plot_multiple_release_timeslines(
        release_timelines=nwb_main_release_timelines,
        add_releases=None,  # Use default of NWBGitInfo.MISSING_RELEASE_TAGS,
        date_range=None,  # Use the default range of
        month_intervals=2,
        fontsize=16,
        title="Timeline of NWB Release")
    plt.savefig(os.path.join(out_dir, 'releases_timeline_nwb_main.pdf'))
    plt.savefig(os.path.join(out_dir, 'releases_timeline_nwb_main.png'), dpi=300)
    plt.close()
    fig = RSTFigure(
        image_path="releases_timeline_nwb_main.png",
        alt="Release timeline of the main NWB repositories",
        width="100%")
    return fig


def __create_nwb_codecov_summary_plot(
        out_dir: str,
        print_status: bool = True):
    """
    Internal helper function used to render the the summary plot of code coverage for NWB core API

    :param out_dir: Output directory
    :param print_status: Print status of creation (Default=True)
    :return: RSTFigure to add to the document
    """

    if print_status:
        PrintHelper.print("PLOTTING: test_coverage_nwb_main", PrintHelper.BOLD)
    codecov_commits = {
        r: CodecovInfo.get_pulls_or_commits(
            NWBGitInfo.GIT_REPOS[r],
            key='commits',
            state='all',
            branch=NWBGitInfo.GIT_REPOS[r].mainbranch)
        for r in ['HDMF', 'PyNWB', 'MatNWB']}
    RenderCodecovInfo.plot_codecov_multiline(
        codecovs=codecov_commits,
        plot_xlim=(NWBGitInfo.NWB2_FIRST_STABLE_RELEASE, datetime.today()),
        fill_alpha=0.2,
        fontsize=16,
        figsize=(12, 6),
        title="Test coverage: NWB core APIs"
    )
    plt.savefig(os.path.join(out_dir, 'test_coverage_nwb_main.pdf'))
    plt.savefig(os.path.join(out_dir, 'test_coverage_nwb_main.png'), dpi=300)
    plt.close()
    fig = RSTFigure(
        image_path="test_coverage_nwb_main.png",
        alt="Code test coverage for the main NWB repositories",
        width=800)
    return fig


def __create_nwb_codestat_summary_rst(
        loc_summary_figure: RSTFigure = None,
        release_timeline_figure: RSTFigure = None,
        codecov_nwb_summary_figure: RSTFigure = None,
        print_status: bool = True):
    """
    Render the RST document with the plots of the NWB summary

    :param out_dir: Output directory
    :param print_status: Print status of creation (Default=True)
    :return: RSTDocument with nwb codestat summary
    """
    if print_status:
        PrintHelper.print("CREATING: code_stats.rst", PrintHelper.BOLD)
    codestats_rst = RSTDocument()
    codestats_rst.add_label("nwbmain-code-statistics")
    codestats_rst.add_section("Code Statistics: NWB Core")
    # Add overview figure
    if loc_summary_figure is not None:
        codestats_rst.add_subsection("Lines of Code: All NWB Codes")
        codestats_rst.add_figure(loc_summary_figure)

    # Add release timeline figure
    if release_timeline_figure is not None:
        codestats_rst.add_subsection("Release Timeline: NWB APIs and Schema")
        codestats_rst.add_figure(release_timeline_figure)

    # Add code coverage figure for main NWB repos
    if codecov_nwb_summary_figure is not None:
        codestats_rst.add_subsection("Test Coverage: NWB APIs")
        codestats_rst.add_figure(codecov_nwb_summary_figure)

    # Add link to the contributors
    codestats_rst.add_subsection("Contributors")
    codestats_rst.add_text(
        "For a listing of all contributors to the various NWB Git repositories see the `contributors.tsv "
        "<https://github.com/NeurodataWithoutBorders/nwb-project-analytics/blob/main/data/contributors.tsv>`_ "
        "file as part of the `nwb-project-analytics "
        "<https://github.com/NeurodataWithoutBorders/nwb-project-analytics>`_ "
        "Git repository.")

    return codestats_rst


def __create_tool_codestat_pages(
        code_figures: dict,
        code_order: list,
        out_dir: str,
        print_status: bool):
    """

    :param code_figures:
    :param code_order:
    :param out_dir: Output directory
    :param print_status: Print status of creation (Default=True)
    :return: RSTDocument with the tool summary
    """

    if print_status:
        PrintHelper.print("CREATING: code_stats_tools.rst", PrintHelper.BOLD)
    tool_codestats_rst = RSTDocument()
    tool_codestats_rst.add_label("code-statistics")
    tool_codestats_rst.add_section("Code Statistics: NWB Tools")
    tool_codestats_rst.add_text(
        "Select a tool or code repository below to view the corresponding code statistics:" +
        tool_codestats_rst.newline +
        tool_codestats_rst.newline)
    # Compile tabs with plots for each repo
    toc_obj = RSTToc(
        maxdepth=1,
        hidden=False,
        titlesonly=True
    )
    for repo_name in code_order:
        tool_page_name = create_toolstat_page(
            out_dir=out_dir,
            repo_name=repo_name,
            repo=NWBGitInfo.GIT_REPOS[repo_name],
            figures=code_figures[repo_name],
            print_status=print_status,
        )
        toc_obj += tool_page_name
    tool_codestats_rst.add_toc(toc_obj)
    return tool_codestats_rst


def create_codestat_pages(out_dir: str,
                          data_dir: str,
                          cloc_path: str = "cloc",
                          load_cached_results: bool = True,
                          cache_results: bool = True,
                          start_date: datetime = None,
                          end_date: datetime = None,
                          print_status: bool = True):
    """
    Main function used to render all pages and figures related to the tool statistics

    :param out_dir: Directory where the RST and image files should be saved to
    :param data_dir: Directory where the data for the code statistics should be cached
    :param cloc_path: Path to the cloc tool if not callable directly via "cloc"
    :param load_cached_results: Load code statists from data_dir if available
    :param cache_results: Save code statistic results to data_dir
    :param start_date: Datetime object with the star tdate for plots. If None then
                       NWBGitInfo.NWB2_START_DATE will be used as default.
    :param end_date: Datetime object with the end date for plots. If None then
                     datetime.today() will be used as default.
    :param print_status: Print status of creation (Default=True)
    """
    # 1. Init the directory
    init_codestat_pages_dir(out_dir=out_dir)

    # 2. Load or create the code statistics with cloc
    if print_status:
        PrintHelper.print("BUILDING Code statistics", PrintHelper.BOLD)
    start_date = NWBGitInfo.NWB2_START_DATE if start_date is None else start_date
    end_date = datetime.today() if end_date is None else end_date
    git_code_stats, summary_stats, per_repo_lang_stats, languages_used_all = GitCodeStats.from_nwb(
        cache_dir=data_dir,
        cloc_path=cloc_path,
        start_date=start_date,
        end_date=end_date,
        read_cache=load_cached_results,
        write_cache=cache_results,
        clean_source_dir=True
    )
    release_timelines = GitHubRepoInfo.releases_from_nwb(
        cache_dir=data_dir,
        read_cache=load_cached_results,
        write_cache=cache_results)

    #  show all NWB2 codes in alphabetical order (and ignore NWB1 codes)
    code_order = [codename for codename in list(sorted(summary_stats['sizes'].keys()))
                  if codename not in NWBGitInfo.NWB1_GIT_REPOS]
    # Collect the figures generated for each code
    code_figures = {repo_name: OrderedDict() for repo_name in code_order}

    # 3. Render all figures
    # 3.1 Render the summary plot of lines-of-code-stats
    loc_summary_figure = __create_loc_summary_plot(
        summary_stats=summary_stats,
        code_order=code_order,
        out_dir=out_dir,
        print_status=print_status)

    # 3.2 Plot per-repo total lines of code statistics broken down by: code, blank, comment
    for repo_name in code_order:
        if print_status:
            PrintHelper.print("PLOTTING: loc_%s" % repo_name, PrintHelper.BOLD)
        ax = RenderClocStats.plot_reposize_code_comment_blank(
            summary_stats=summary_stats,
            repo_name=repo_name,
            title="Lines of Code: %s" % repo_name
        )
        plt.savefig(os.path.join(out_dir, "loc_%s.pdf" % repo_name))
        plt.savefig(os.path.join(out_dir, "loc_%s.png" % repo_name), dpi=300)
        plt.close()
        del ax
        code_figures[repo_name]['loc'] = RSTFigure(
            image_path="loc_%s.png" % repo_name,
            alt="Lines of Code: %s" % repo_name,
            width="100%")

    # 3.3 Plot per-repo language breakdown
    # Iterate through all repos and plot the per-language LOC stats for each repo
    for repo_name in code_order:
        if print_status:
            PrintHelper.print("PLOTTING: loc_language_%s" % repo_name, PrintHelper.BOLD)
        ax = RenderClocStats.plot_reposize_language(
            per_repo_lang_stats=per_repo_lang_stats,
            languages_used_all=languages_used_all,
            repo_name=repo_name,
            figsize=None,
            fontsize=18,
            title="Lines of Code: %s" % repo_name)
        plt.savefig(os.path.join(out_dir, "loc_language_%s.png" % repo_name), dpi=300)
        plt.close()
        del ax
        code_figures[repo_name]['lang_loc'] = RSTFigure(
            image_path="loc_language_%s.png" % repo_name,
            alt="Lines of Code per Language: %s" % repo_name,
            width="100%")

    # 3.4 Render summary release timeline
    release_timeline_figure = __create_nwb_release_timeline_summary_plot(
        release_timelines=release_timelines,
        out_dir=out_dir,
        print_status=print_status)

    # 3.5 Render per repo release timeline
    github_repo_infos = NWBGitInfo.GIT_REPOS.get_info_objects()
    for repo_name in code_order:
        names, dates = release_timelines[repo_name]
        if len(names) == 0 and NWBGitInfo.MISSING_RELEASE_TAGS.get(repo_name, None) is None:
            if print_status:
                PrintHelper.print("SKIPPING: release_timeline_%s" % repo_name, PrintHelper.BOLD + PrintHelper.OKBLUE)
            continue
        elif print_status:
            PrintHelper.print("PLOTTING: release_timeline_%s" % repo_name, PrintHelper.BOLD)
        ax = RenderReleaseTimeline.plot_release_timeline(
            repo_name=repo_name,
            versions=release_timelines[repo_name][0],
            dates=release_timelines[repo_name][1],
            figsize=(18, 6),
            fontsize=16,
            month_intervals=3,
            xlim=None,
            ax=None,
            title_on_yaxis=False,
            # Add missing NWB releases if necessary
            add_releases=NWBGitInfo.MISSING_RELEASE_TAGS.get(repo_name, None))
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, 'releases_timeline_%s.pdf' % repo_name))
        plt.savefig(os.path.join(out_dir, 'releases_timeline_%s.png' % repo_name), dpi=300)
        plt.close()
        del ax
        code_figures[repo_name]['releases'] = RSTFigure(
            image_path="releases_timeline_%s.png" % repo_name,
            alt="Release times: %s" % repo_name,
            width="100%")
    """
    # 3.6 Code coverage stats for main repos
    codecov_nwb_summary_figure = __create_nwb_codecov_summary_plot(
        out_dir=out_dir,
        print_status=print_status)

    # 3.7 Code coverage stats per repo
    for repo_name in code_order:
        print("HERE0", repo_name)
        codecov_commits = CodecovInfo.get_pulls_or_commits(
                NWBGitInfo.GIT_REPOS[repo_name],
                key='commits',
                state='all',
                branch=NWBGitInfo.GIT_REPOS[repo_name].mainbranch)
        if len(codecov_commits) > 0:
            if print_status:
                PrintHelper.print("PLOTTING: test_coverage_%s" % repo_name, PrintHelper.BOLD)
            print(codecov_commits)
            print("HERE1")
            _ = RenderCodecovInfo.plot_codecov_individual(
                codecovs={repo_name: codecov_commits},
                plot_xlim=None,
                fontsize=16,
                figsize=(14, 6),
                title="Test Coverage: %s" % repo_name
            )
            print("HERE2")
            plt.savefig(os.path.join(out_dir, 'test_coverage_%s.pdf' % repo_name))
            plt.savefig(os.path.join(out_dir, 'test_coverage_%s.png' % repo_name), dpi=300)
            plt.close()
            code_figures[repo_name]['codecov'] = RSTFigure(
                image_path="test_coverage_%s.png" % repo_name,
                alt="Test coverage: %s" % repo_name,
                width="100%")
        else:
            PrintHelper.print("SKIPPING: test_coverage_%s" % repo_name, PrintHelper.BOLD + PrintHelper.OKBLUE)
    """
    codecov_nwb_summary_figure = None

    # 4. Create the RST document
    codestats_rst = __create_nwb_codestat_summary_rst(
        loc_summary_figure=loc_summary_figure,
        release_timeline_figure=release_timeline_figure,
        codecov_nwb_summary_figure=codecov_nwb_summary_figure,
        print_status=print_status)
    # Write the summary RST documents
    codestats_rst.write(os.path.join(out_dir, "code_stats_main.rst"))

    # 5. Create the RST pages for the individual tools.
    # Note, the RST pages for the individual tools are written by _create_tool_codestat_pages directly
    tool_codestats_rst = __create_tool_codestat_pages(
        code_figures=code_figures,
        code_order=code_order,
        out_dir=out_dir,
        print_status=print_status)
    # Write the tools summary page.
    tool_codestats_rst.write(os.path.join(out_dir, "code_stats_tools.rst"))
