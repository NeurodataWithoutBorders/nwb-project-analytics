"""Script for creating rst pages and figures with NWB code statistics"""
import os
import shutil
from datetime import datetime
from matplotlib import pyplot as plt
from collections import OrderedDict

from nwb_project_analytics.codestats import GitCodeStats
from nwb_project_analytics.gitstats import NWBGitInfo
from nwb_project_analytics.codecovstats import CodecovInfo
from nwb_project_analytics.renderstats import (
    RenderClocStats,
    RenderReleaseTimeline,
    RenderCodecovInfo)
from hdmf_docutils.doctools.output import PrintHelper
from hdmf_docutils.doctools.rst import RSTDocument


def init_codestat_pages_dir(out_dir):
    """
    Delete out_dir and all its contents and create a new clean out_dir
    :param out_dir: Directory to be removed
    :return:
    """
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    os.mkdir(out_dir)


def create_codestat_pages(out_dir: str,   # noqa: C901
                          data_dir: str,
                          cloc_path: str = "cloc",
                          load_cached_results: bool = True,
                          cache_results: bool = True,
                          start_date: datetime = None,
                          end_date: datetime = None,
                          print_status: bool = True):
    """

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
        write_cache=cache_results
    )
    #  show all NWB2 codes in alphabetical order (and ignore NWB1 codes)
    codeorder = [codename for codename in list(sorted(summary_stats['sizes'].keys()))
                 if codename not in NWBGitInfo.NWB1_GIT_REPOS]

    # 3. Render all figures
    # 3.1 Render the summary plot of lines-of-code-stats
    if print_status:
        PrintHelper.print("PLOTTING: nwb_reposize_all", PrintHelper.BOLD)
    ax = RenderClocStats.plot_cloc_sizes_stacked_area(
        summary_stats=summary_stats,
        order=codeorder,   # show all NWB2 codes in alphabetical order (and ignore NWB1 codes)
        colors=None,  # use default color
        title="NWB code repository sizes in lines-of-code (LOC)",
        fontsize=20)
    plt.savefig(os.path.join(out_dir, "nwb_reposize_all.pdf"))
    plt.savefig(os.path.join(out_dir, "nwb_reposize_all.png"), dpi=300)
    plt.close()
    del ax

    # 3.2 Plot per-repo total lines of code statistics broken down by: code, blank, comment
    loc_figures = {}
    for repo_name in codeorder:
        if print_status:
            PrintHelper.print("PLOTTING: loc_%s" % repo_name, PrintHelper.BOLD)
        ax = RenderClocStats.plot_reposize_code_comment_blank(
            summary_stats=summary_stats,
            repo_name=repo_name,
            title="Lines of Code: %s" % repo_name
        )
        loc_figures[repo_name] = "loc_%s.png" % repo_name
        plt.savefig(os.path.join(out_dir, "loc_%s.pdf" % repo_name))
        plt.savefig(os.path.join(out_dir, "loc_%s.png" % repo_name), dpi=300)
        plt.close()
        del ax

    # 3.3 Plot per-repo language breakdown
    loc_lang_figures = {}
    # Iterate through all repos and plot the per-language LOC stats for each repo
    for repo_name in codeorder:
        if print_status:
            PrintHelper.print("PLOTTING: loc_language_%s" % repo_name, PrintHelper.BOLD)
        ax = RenderClocStats.plot_reposize_language(
            per_repo_lang_stats=per_repo_lang_stats,
            languages_used_all=languages_used_all,
            repo_name=repo_name,
            figsize=None,
            fontsize=18,
            title="Lines of Code: %s" % repo_name)
        loc_lang_figures[repo_name] = "loc_language_%s.png" % repo_name
        plt.savefig(os.path.join(out_dir, "loc_language_%s.pdf" % repo_name))
        plt.savefig(os.path.join(out_dir, "loc_language_%s.png" % repo_name), dpi=300)
        plt.close()
        del ax

    # 3.4 Render summary release timeline
    PrintHelper.print("PLOTTING: releases_timeline_nwb_main", PrintHelper.BOLD)
    github_repo_infos = NWBGitInfo.GIT_REPOS.get_info_objects()
    release_timeline_repos = OrderedDict(
        [(k, github_repo_infos[k])
         for k in ['PyNWB', 'HDMF', 'MatNWB', 'NWB_Schema']
         ]
    )
    RenderReleaseTimeline.plot_multiple_release_timeslines(
        github_repo_infos=release_timeline_repos,
        add_releases=None,  # Use default of NWBGitInfo.MISSING_RELEASE_TAGS,
        date_range=None,  # Use the default range of
        month_intervals=2,
        fontsize=16,
        title="Timeline of NWB Release")
    plt.savefig(os.path.join(out_dir, 'releases_timeline_nwb_main.pdf'))
    plt.savefig(os.path.join(out_dir, 'releases_timeline_nwb_main.png'), dpi=300)
    plt.close()

    # 3.5 Render per repo release timeline
    release_timeline_figures = {}
    for repo_name in codeorder:
        names, dates = github_repo_infos[repo_name].get_release_names_and_dates()
        if len(names) == 0 and NWBGitInfo.MISSING_RELEASE_TAGS.get(repo_name, None) is None:
            if print_status:
                PrintHelper.print("SKIPPING: release_timeline_%s" % repo_name, PrintHelper.BOLD + PrintHelper.OKBLUE)
            release_timeline_figures[repo_name] = None
            continue
        elif print_status:
            PrintHelper.print("PLOTTING: release_timeline_%s" % repo_name, PrintHelper.BOLD)
        ax = RenderReleaseTimeline.plot_release_timeline(
            repo_info=github_repo_infos[repo_name],
            figsize=(18, 6),
            fontsize=16,
            month_intervals=3,
            xlim=None,
            ax=None,
            title_on_yaxis=False,
            # Add missing NWB releases if necessary
            add_releases=NWBGitInfo.MISSING_RELEASE_TAGS.get(repo_name, None))
        plt.tight_layout()
        release_timeline_figures[repo_name] = 'releases_timeline_%s.png' % repo_name
        plt.savefig(os.path.join(out_dir, 'releases_timeline_%s.pdf' % repo_name))
        plt.savefig(os.path.join(out_dir, 'releases_timeline_%s.png' % repo_name), dpi=300)
        plt.close()
        del ax

    # 3.6 Code coverage stats for main repos
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
        figsize=(12, 6))
    plt.savefig(os.path.join(out_dir, 'test_coverage_nwb_main.pdf'))
    plt.savefig(os.path.join(out_dir, 'test_coverage_nwb_main.png'), dpi=300)
    plt.close()

    # 3.7 Code coverage stats per repo
    test_coverage_figures = {}
    for repo_name in codeorder:
        codecov_commits = CodecovInfo.get_pulls_or_commits(
                NWBGitInfo.GIT_REPOS[repo_name],
                key='commits',
                state='all',
                branch=NWBGitInfo.GIT_REPOS[repo_name].mainbranch)
        if len(codecov_commits) > 0:
            if print_status:
                PrintHelper.print("PLOTTING: test_coverage_%s" % repo_name, PrintHelper.BOLD)
            _ = RenderCodecovInfo.plot_codecov_individual(
                codecovs={repo_name: codecov_commits},
                plot_xlim=None,
                fontsize=16,
                figsize=(14, 6)
            )
            test_coverage_figures[repo_name] = "test_coverage_%s.png" % repo_name
            plt.savefig(os.path.join(out_dir, 'test_coverage_%s.pdf' % repo_name))
            plt.savefig(os.path.join(out_dir, 'test_coverage_%s.png' % repo_name), dpi=300)
            plt.close()
        else:
            PrintHelper.print("SKIPPING: test_coverage_%s" % repo_name, PrintHelper.BOLD + PrintHelper.OKBLUE)
            test_coverage_figures[repo_name] = None

    # 4. Create the RST document
    if print_status:
        PrintHelper.print("CREATING: code_stats.rst", PrintHelper.BOLD)
    codestats_rst = RSTDocument()
    codestats_rst.add_label("nwb-code-statistics")
    codestats_rst.add_section("NWB Code Statistics")
    # Add overview figure
    codestats_rst.add_figure(
        img="nwb_reposize_all.png",
        alt="NWB code repository sizes",
        width=800
    )

    # Add release timeline figure
    codestats_rst.add_figure(
        img="releases_timeline_nwb_main.png",
        alt="Release timeline of the main NWB repositories",
        width=800
    )

    # Add code coverage figure for main NWB repos
    codestats_rst.add_figure(
        img="test_coverage_nwb_main.png",
        alt="Code test coverage for the main NWB repositories",
        width=800
    )
    codestats_rst.write(os.path.join(out_dir, "code_stats_main.rst"))

    if print_status:
        PrintHelper.print("CREATING: code_stats_tools.rst", PrintHelper.BOLD)
    tool_codestats_rst = RSTDocument()
    tool_codestats_rst.add_label("tools-statistics")
    tool_codestats_rst.add_section("Tool Statistics")
    tool_codestats_rst.add_text(
        "Select a tool using the tabs below to view the corresponding code statistics:" +
        tool_codestats_rst.newline +
        tool_codestats_rst.newline)
    # Compile tabs with plots for each repo
    tab_text = tool_codestats_rst.newline
    for repo_name in codeorder:
        # Add a tab
        tab_text += ".. tab:: %s" % repo_name
        tab_text += tool_codestats_rst.newline
        # Add lines of code figures
        fig_doc = RSTDocument()
        fig_doc.add_figure(
            img=loc_figures[repo_name],
            alt="Lines of Code: %s" % repo_name,
            width=800)
        fig_doc.add_figure(
            img=loc_lang_figures[repo_name],
            alt="Lines of Code per Language: %s" % repo_name,
            width=800)
        if release_timeline_figures[repo_name] is not None:
            fig_doc.add_figure(
                img=release_timeline_figures[repo_name],
                alt="Release times: %s" % repo_name,
                width=800)
        if test_coverage_figures[repo_name] is not None:
            fig_doc.add_figure(
                img=test_coverage_figures[repo_name],
                alt="Test coverage: %s" % repo_name,
                width=800)
        tab_text += codestats_rst.indent_text(fig_doc.document)
    tool_codestats_rst.add_admonitions(atype='tabs', text=tab_text)
    tool_codestats_rst.write(os.path.join(out_dir, "code_stats_tools.rst"))
