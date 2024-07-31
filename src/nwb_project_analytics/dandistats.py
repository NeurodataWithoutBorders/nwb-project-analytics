"""
Compute DANDI statistics for NWB projects
"""

from dandi.dandiapi import DandiAPIClient
from collections import defaultdict
from tqdm import tqdm
import numpy as np
import pandas as pd
import os
from matplotlib import pyplot as plt
from matplotlib import dates as mpl_dates
from hdmf_docutils.doctools.output import PrintHelper
from hdmf_docutils.doctools.rst import RSTDocument, RSTFigure
import datetime


class DANDIStats:

    # Map NWB neurodata_types to types of physiology ecephys, ophys, icephys
    NEURODATA_TYPE_MAP = dict(
        ecephys=["LFP", "Units", "ElectricalSeries"],
        ophys=["PlaneSegmentation", "TwoPhotonSeries", "ImageSegmentation"],
        icephys=[
            "PatchClampSeries",
            "VoltageClampSeries",
            "CurrentClampSeries",
            "CurrentClampStimulusSeries",
        ],
    )

    # Dict with mappings used to clean up species
    SPECIES_REPLACEMENT = {
        "Mus musculus - House mouse": "House mouse",
        "Rattus norvegicus - Norway rat": "Rat",
        "Brown rat": "Rat",
        "Rat; norway rat; rats; brown rat": "Rat",
        "Homo sapiens - Human": "Human",
        "Drosophila melanogaster - Fruit fly": "Fruit fly",
        "Danio rerio - Leopard danio": "Zebrafish",
        "Macaca mulatta - Rhesus monkey": "Rhesus monkey",
        "Danio rerio - Zebra fish": "Zebrafish",
        "Macaca nemestrina - Pig-tailed macaque": "Pig-tailed macaque",
        "Cricetulus griseus - Cricetulus aureus": "Chinese hamster",
        "Caenorhabditis elegans": "C. elegans",
        "Canis lupus familiaris - Dog": "Dog",
        "Oryctolagus cuniculus - Rabbits": "Rabbit",
        "Bos taurus - Cattle": "Cattle",
        "Macaca nemestrina - Pigtail macaque": "Pigtail macaque",
        "Ooceraea biroi - Clonal raider ant": "Clonal raider ant",
    }

    # Name of the file where dandi nwb statistics are cached
    DANDI_NWB_STATS_FILENAME = "dandi_nwb_stats.tsv"

    @staticmethod
    def is_nwb(metadata):
        """Check if the dandiset is a NWB dandiset"""
        return any(
            x['identifier'] == 'RRID:SCR_015242'
            for x in metadata['assetsSummary'].get('dataStandard', {})
        )

    @staticmethod
    def has_related_publication(metadata):
        """Check if the dandiset has related publications"""
        return "relatedResource" in metadata and any(
            x.get("relation") == "dcite:IsDescribedBy" for x in metadata["relatedResource"])

    @staticmethod
    def cached(output_dir):
        """Check if a complete cached version of this class exists at output_dir"""
        return os.path.exists(os.path.join(output_dir,  DANDIStats.DANDI_NWB_STATS_FILENAME))

    @classmethod
    def compute_dandi_nwb_stats(cls,
                                cache_dir: str,
                                read_cache: bool = True,
                                write_cache: bool = True,
                                print_status: bool = True):
        """
        Compute the NWB statistics for all DANDI datasets

        :param cache_dir: Path to the director where the files with the cached results
                          are stored or should be written to
        :param read_cache: Bool indicating whether results should be loaded from cache
                           if cached files exists at cache_dir. NOTE: If read_cache is
                           True and files are in the cache then the results will be
                           loaded without checking results (e.g., whether results
                           in the cache are complete and up-to-date).
        :param write_cache: Bool indicating whether to write the results to the cache.
        :param print_status: Print status of creation (Default=True)
        """
        cache_filename = os.path.join(cache_dir, DANDIStats.DANDI_NWB_STATS_FILENAME)
        if cls.cached(cache_dir) and read_cache:
            if print_status:
                PrintHelper.print("LOADING DANDI NWB statistics from %s" % cache_filename, PrintHelper.BOLD)
            return pd.read_csv(
                cache_filename,
                sep="\t")
        if print_status:
            PrintHelper.print("BUILDING DANDI NWB statistics", PrintHelper.BOLD)

        client = DandiAPIClient()
        dandisets = list(client.get_dandisets())

        data = defaultdict(list)
        for dandiset in tqdm(dandisets):
            dandiset = dandiset.for_version("draft")
            identifier = dandiset.identifier
            metadata = dandiset.get_raw_metadata()

            if not cls.is_nwb(metadata) or not dandiset.draft_version.size:
                continue
            data["identifier"].append(identifier)
            data["created"].append(dandiset.created)
            data["modified"].append(dandiset.modified)
            data["size"].append(dandiset.draft_version.size)
            if "species" in metadata["assetsSummary"] and len(metadata["assetsSummary"]["species"]):
                data["species"].append(metadata["assetsSummary"]["species"][0]["name"])
            else:
                data["species"].append(np.nan)

            data["nauthors"].append(
                sum(x.get('schemaKey', []) == "Person" for x in
                    metadata["contributor"]) if "contributor" in metadata else 0
            )

            for modality, ndtypes in cls.NEURODATA_TYPE_MAP.items():
                data[modality].append(
                    any(x in ndtypes for x in metadata["assetsSummary"]["variableMeasured"])
                )

            data["numberOfSubjects"].append(metadata["assetsSummary"].get("numberOfSubjects", np.nan))
            data["numberOfFiles"].append(metadata["assetsSummary"].get("numberOfFiles", np.nan))
            data["has_related_pub"].append(cls.has_related_publication(metadata))

        dandistats_df = pd.DataFrame.from_dict(data)

        # Clean up species
        for key, val in cls.SPECIES_REPLACEMENT.items():
            dandistats_df["species"] = dandistats_df["species"].replace(key, val)

        if write_cache:
            if print_status:
                PrintHelper.print("SAVING DANDI NWB statistics to %s" % cache_filename, PrintHelper.BOLD)
            dandistats_df.to_csv(cache_filename, sep="\t")

        return dandistats_df

    @staticmethod
    def plot_species_histogram(dandistats_df: pd.DataFrame,
                               figure_path: str):
        """
        Plot histogram of species distribution across NWB dandisets

        :param dandistats_df: Datafram with DANDI NWB stats computed by compute_dandi_nwb_stats
        :param figure_path: Path where the figure should be saved
        """
        fig, ax = plt.subplots(figsize=(3, 3))
        vals = dandistats_df["species"]
        # Only show shorthand label. E.g. ,replace "Procambarus clarkii - Red swamp crayfish" with "Red swamp crayfish"
        for name in dandistats_df["species"].value_counts().keys():
            if " - " in name:
                vals = vals.replace(name, name.split(" - ")[1])

        ax = vals.value_counts().plot.barh(figsize=(3, 3))
        ax.invert_yaxis()
        ax.set_xlabel("# of NWB Dandisets")
        ax.set_ylabel("Species")
        plt.grid(True, which='both', axis='both', color='gray', linestyle='--', linewidth=0.75, zorder=0)
        ax.yaxis.grid(False)
        ax.figure.savefig(
            figure_path,
            bbox_inches="tight",
            dpi=300,
            transparent=True,
        )

    @staticmethod
    def plot_modality_histogram(dandistats_df: pd.DataFrame,
                                figure_path: str):
        """
        Plot histogram of modalities ecephys, ophys, icephys  distribution across NWB dandisets

        :param dandistats_df: Datafram with DANDI NWB stats computed by compute_dandi_nwb_stats
        :param figure_path: Path where the figure should be saved
        """
        fig, ax = plt.subplots(figsize=(1, 3))
        dandistats_df[["ecephys", "ophys", "icephys"]].sum().plot.bar(ax=ax)
        ax.set_xlabel("Modality")
        ax.set_ylabel("# of NWB Dandisets")
        plt.grid(True, which='both', axis='both', color='gray', linestyle='--', linewidth=0.75, zorder=0)
        ax.xaxis.grid(False)
        ax.figure.savefig(
            figure_path,
            bbox_inches="tight",
            dpi=300,
            transparent=True,
        )

    @staticmethod
    def plot_dandiset_size_histogram(dandistats_df: pd.DataFrame,
                                     figure_path: str):
        """
        Plot histogram of data sizes across NWB dandisets

        :param dandistats_df: Datafram with DANDI NWB stats computed by compute_dandi_nwb_stats
        :param figure_path: Path where the figure should be saved
        """
        logsize = np.log10(dandistats_df["size"])
        fig, ax = plt.subplots(figsize=(3, 3))
        ax = logsize.plot.hist(bins=20, ax=ax)
        ax.set_xticks([3, 6, 9, 12, 15])
        ax.set_xticklabels(["KB", "MB", "GB", "TB", "PB"])
        ax.set_xlabel("Total Dandiset size")
        ax.set_ylabel("# of NWB Dandisets")
        plt.grid(True, which='both', axis='both', color='gray', linestyle='--', linewidth=0.75, zorder=0)
        ax.xaxis.grid(False)
        ax.figure.savefig(
            figure_path,
            bbox_inches="tight",
            dpi=300,
            transparent=True,
        )

    @staticmethod
    def plot_number_of_dandisets_by_date(dandistats_df: pd.DataFrame,
                                         figure_path: str):
        """
        Plot curve-plot of the number of DANDI NWB datasets over time

        :param dandistats_df: Datafram with DANDI NWB stats computed by compute_dandi_nwb_stats
        :param figure_path: Path where the figure should be saved
        """
        fig, ax = plt.subplots(figsize=(4, 3))

        dates = dandistats_df['created']
        dates = mpl_dates.date2num(dates)
        ax.plot(dates,
                np.arange(len(dandistats_df)),
                '-k.',
                linewidth=0.5)
        for label in ax.get_xticklabels(which='major'):
            label.set(rotation=30, horizontalalignment='right')
        ax.set_ylabel('# of NWB Dandisets')
        ax.set_xlabel("Date created")
        # Formatting the x-axis to show dates correctly
        plt.gca().xaxis.set_major_locator(mpl_dates.DayLocator(interval=180))
        plt.gca().xaxis.set_major_formatter(mpl_dates.DateFormatter('%Y-%m-%d'))
        # Rotate and format the date labels
        plt.gcf().autofmt_xdate()
        plt.grid(True, which='both', axis='both', color='gray', linestyle='--', linewidth=0.75, zorder=0)
        ax.figure.savefig(
            figure_path,
            bbox_inches="tight",
            dpi=300,
            transparent=True)

    @staticmethod
    def plot_size_of_dandisets_by_date(dandistats_df: pd.DataFrame,
                                       figure_path: str):
        """
        Plot curve-plot of the total size of DANDI NWB datasets over time

        :param dandistats_df: Datafram with DANDI NWB stats computed by compute_dandi_nwb_stats
        :param figure_path: Path where the figure should be saved
        """
        fig, ax = plt.subplots(figsize=(4, 3))
        order = np.argsort(dandistats_df['modified'])
        dates = mpl_dates.date2num(dandistats_df['modified'][order])
        ax.plot(dates,
                dandistats_df['size'][order].cumsum() / 10 ** 12,
                '-k.',
                linewidth=0.5)
        for label in ax.get_xticklabels(which='major'):
            label.set(rotation=30, horizontalalignment='right')
        ax.set_xlabel("Date")
        _ = ax.set_ylabel("TB of NWB data on Dandi")
        # Formatting the x-axis to show dates correctly
        plt.gca().xaxis.set_major_locator(mpl_dates.DayLocator(interval=180))
        plt.gca().xaxis.set_major_formatter(mpl_dates.DateFormatter('%Y-%m-%d'))
        # Rotate and format the date labels
        plt.gcf().autofmt_xdate()
        plt.grid(True, which='both', axis='both', color='gray', linestyle='--', linewidth=0.75, zorder=0)
        ax.figure.savefig(
            figure_path,
            bbox_inches="tight",
            dpi=300,
            transparent=True)

    @staticmethod
    def plot_number_of_nwbfiles_by_date(dandistats_df: pd.DataFrame,
                                        figure_path: str):
        """
        Plot curve-plot of the total number of NWB files in  DANDI datasets over time

        :param dandistats_df: Datafram with DANDI NWB stats computed by compute_dandi_nwb_stats
        :param figure_path: Path where the figure should be saved
        """
        fig, ax = plt.subplots(figsize=(4, 3))
        order = np.argsort(dandistats_df['modified'])
        dates = mpl_dates.date2num(dandistats_df['modified'][order])
        ax.plot(dates,
                dandistats_df['numberOfFiles'][order].cumsum(),
                '-k.',
                linewidth=0.5)
        for label in ax.get_xticklabels(which='major'):
            label.set(rotation=30, horizontalalignment='right')
        ax.set_xlabel("Date")
        _ = ax.set_ylabel("# files in NWB dandisets")
        # Formatting the x-axis to show dates correctly
        plt.gca().xaxis.set_major_locator(mpl_dates.DayLocator(interval=180))
        plt.gca().xaxis.set_major_formatter(mpl_dates.DateFormatter('%Y-%m-%d'))
        # Rotate and format the date labels
        plt.gcf().autofmt_xdate()
        plt.grid(True, which='both', axis='both', color='gray', linestyle='--', linewidth=0.75, zorder=0)
        ax.figure.savefig(
            figure_path,
            bbox_inches="tight",
            dpi=300,
            transparent=True)

    @classmethod
    def create_dandistats_pages(cls,
                                out_dir: str,
                                data_dir: str,
                                load_cached_results: bool = True,
                                cache_results: bool = True,
                                print_status: bool = True):
        """
        Render all pages and figures related to the dandi nwb statistics

        :param out_dir: Directory where the RST and image files should be saved to
        :param data_dir: Directory where the data for the code statistics should be cached
        :param load_cached_results: Load code statists from data_dir if available
        :param cache_results: Save code statistic results to data_dir
        :param print_status: Print status of creation (Default=True)
        """
        dandistats_df = cls.compute_dandi_nwb_stats(cache_dir=data_dir,
                                                    read_cache=load_cached_results,
                                                    write_cache=cache_results,
                                                    print_status=print_status)

        current_datetime = datetime.datetime.now()
        formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M:%S")

        # Render all the figures
        if print_status:
            PrintHelper.print("CREATING DANDI NWB figures and rst", PrintHelper.BOLD)
        dandistat_figures = []
        dandistats_rst = RSTDocument()
        dandistats_rst.add_label("dandi-statistics")
        dandistats_rst.add_section("DANDI: NWB Data Statistics")
        dandistats_rst.add_text(dandistats_rst.newline)
        dandistats_rst.add_text(dandistats_rst.newline)
        dandistats_rst.add_text(f"Plots rendered on: {formatted_datetime}")
        dandistats_rst.add_text(dandistats_rst.newline)
        dandistats_rst.add_text(dandistats_rst.newline)
        dandistats_rst.add_subsection("NWB data on DANDI over time")
        # Figure 1
        count_figpath = os.path.join(out_dir, 'nwb_dandiset_count_by_date.png')
        cls.plot_number_of_dandisets_by_date(dandistats_df=dandistats_df,
                                             figure_path=count_figpath)
        dandistat_figures.append(
            RSTFigure(
                image_path=os.path.basename(count_figpath),
                alt="Number of NWB dandisets over time",
                width="100%")
        )
        dandistats_rst.add_figure(figure=dandistat_figures[-1])
        # Figure 2
        sizebytime_figpath = os.path.join(out_dir, 'nwb_dandiset_size_by_date.png')
        cls.plot_size_of_dandisets_by_date(dandistats_df=dandistats_df,
                                           figure_path=sizebytime_figpath)
        dandistat_figures.append(
            RSTFigure(
                image_path=os.path.basename(sizebytime_figpath),
                alt="Size of NWB dandisets by date",
                width="100%")
        )
        dandistats_rst.add_figure(figure=dandistat_figures[-1])
        # Figure 3
        nwb_count_figpath = os.path.join(out_dir, 'nwb_dandiset_nwbcount_by_date.png')
        cls.plot_number_of_nwbfiles_by_date(dandistats_df=dandistats_df,
                                            figure_path=nwb_count_figpath)
        dandistat_figures.append(
            RSTFigure(
                image_path=os.path.basename(nwb_count_figpath),
                alt="Number of NWB files in dandisets over time",
                width="100%")
        )
        dandistats_rst.add_figure(figure=dandistat_figures[-1])
        # Figure 4
        dandistats_rst.add_subsection("Histograms of properties of NWB data on DANDI")
        species_figpath = os.path.join(out_dir, 'nwb_dandiset_species_hist.png')
        cls.plot_species_histogram(dandistats_df=dandistats_df,
                                   figure_path=species_figpath)
        dandistat_figures.append(
            RSTFigure(
                image_path=os.path.basename(species_figpath),
                alt="Distribution of species in NWB dandisets",
                width="100%")
        )
        dandistats_rst.add_figure(figure=dandistat_figures[-1])
        # Figure 5
        modality_figpath = os.path.join(out_dir, 'nwb_dandiset_modality_hist.png')
        cls.plot_modality_histogram(dandistats_df=dandistats_df,
                                    figure_path=modality_figpath)
        dandistat_figures.append(
            RSTFigure(
                image_path=os.path.basename(modality_figpath),
                alt="NWB dandisets modality distribution",
                width="50%")
        )
        dandistats_rst.add_figure(figure=dandistat_figures[-1])
        # Figure 6
        size_figpath = os.path.join(out_dir, 'nwb_dandiset_size_hist.png')
        cls.plot_dandiset_size_histogram(dandistats_df=dandistats_df,
                                         figure_path=size_figpath)
        dandistat_figures.append(
            RSTFigure(
                image_path=os.path.basename(size_figpath),
                alt="NWB dandisets size distribution",
                width="100%")
        )
        dandistats_rst.add_figure(figure=dandistat_figures[-1])

        # Save the RST file to disk
        dandistats_rst.write(os.path.join(out_dir, "dandi_nwb_stats.rst"))
