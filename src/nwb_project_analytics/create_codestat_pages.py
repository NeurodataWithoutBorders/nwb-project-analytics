"""Script for creating rst pages and figures with NWB code statistics"""
import os
import shutil
from datetime import datetime
from matplotlib import pyplot as plt

from nwb_project_analytics.codestats import GitCodeStats
from nwb_project_analytics.gitstats import NWBGitInfo
from nwb_project_analytics.renderstats import RenderClocStats
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


def create_codestat_pages(out_dir: str,
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
    # Init the directory
    init_codestat_pages_dir(out_dir=out_dir)

    # Load or create the code statistics with cloc
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

    # Render the summary plot
    if print_status:
        PrintHelper.print("PLOTTING: nwb_reposize_all", PrintHelper.BOLD)
    ax = RenderClocStats.plot_cloc_sizes_stacked_area(
        summary_stats=summary_stats,
        order=None,   # show all in alphabetical order
        colors=None,  # use default color
        title="NWB code repository sizes in lines-of-code (LOC)",
        fontsize=20)
    plt.savefig(os.path.join(out_dir, "nwb_reposize_all.pdf"))
    plt.savefig(os.path.join(out_dir, "nwb_reposize_all.png"), dpi=300)
    plt.close()
    del ax

    # Plot per-repo total lines of code statistics broken down by: code, blank, comment
    loc_figures = {}
    for repo_name in summary_stats['codes'].keys():
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

    # Plot per-repo language breakdown
    loc_lang_figures = {}
    # Iterate through all repos and plot the per-language LOC stats for each repo
    for repo_name in per_repo_lang_stats.keys():
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

    # Create the RST document
    codestats_rst = RSTDocument()
    codestats_rst.add_label("nwb-code-statistics")
    codestats_rst.add_section("NWB Code Statistics")
    # Add overview figure
    codestats_rst.add_subsection("Overview")
    codestats_rst.add_figure(
        img="nwb_reposize_all.png",
        alt="NWB code repository sizes",
        width=800
    )

    # Add the line of code statistics for all repos
    codestats_rst.add_subsection("Lines of Code")
    tab_text = codestats_rst.newline
    for repo_name in sorted(per_repo_lang_stats.keys()):
        # Add a tab
        tab_text += ".. tab:: %s" % repo_name
        tab_text += codestats_rst.newline
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
        tab_text += codestats_rst.indent_text(fig_doc.document)
    codestats_rst.add_admonitions(atype='tabs', text=tab_text)
    codestats_rst.write(os.path.join(out_dir, "code_stats.rst"))
