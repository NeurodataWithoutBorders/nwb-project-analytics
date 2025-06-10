=====================
nwb-project-analytics
=====================

Repository for collecting analytics and scripts related to the NWB project.

The NWB project maintains and contributes to a large number of codes
related to NWB. The goal of this effort is to help  developers to get a
quick overview of the state of NWB code repositories. See, e.g., the `code health page <https://github.com/NeurodataWithoutBorders/nwb-project-analytics/blob/main/docs/source/code_health.rst>`_

**Status:** This project is under active development. The code is in the alpha development phase.

How to use nwb-project-analytics (the docs)
===========================================

All main NWB analytics are compiled automatically when building the ``docs``

1. Create a virtual environment (option)

.. code-block:: bash:

    conda create --name nwb_analytics_env python=3.13
    conda activate nwb_analytics_env

2. Install ``cloc`` (see `here <https://github.com/AlDanial/cloc#install-via-package-manager>`_)
   (only needed when you want to update the cloc code statistics in ``data/``)

3. Install the tools via

.. code-block:: bash

    git clone https://github.com/NeurodataWithoutBorders/nwb-project-analytics.git
    cd nwb-project-analytics
    pip install -e ".[docs]"

4. Build the docs

.. code-block:: bash

    cd docs
    make html
    open build/html/index.html

How to force rebuild of all figures and apidoc
==============================================

.. code-block:: bash

    cd docs
    make allclean

Using the ``make allclean`` command removes all auto-generated figures and rst files in the ``docs/source`` directory (specifically ``docs/source/code_stat_pages`` and ``docs/source/nwb_project_analytics.*rst``) as well as all builds from ``docs/builds``. When rebuilding the docs (e.g., via ``make html``) the files will be regenerated (using the data cached in ``data/``).

How to manually update the ``data/``
==================================

On this repo, the information cached in ``data/`` is automatically updated nighlty by the `build_analytics_data.yml <https://github.com/NeurodataWithoutBorders/nwb-project-analytics/blob/main/.github/workflows/build_analytics_data.yml>`_ GitHub Action. To manually update the statistics cached in ``data/``, simply remove the cached results and build the docs:

.. code-block:: bash

    rm data/cloc_stats.yaml
    rm data/commit_stats.yaml
    rm data/git_paths.yaml
    rm data/release_timelines.yaml
    rm data/contributors.tsv
    cd docs
    make html

After completing the update, commit the updated data to the repo

.. code-block:: bash

    git commit -m "Updated code statistics data" ./data/*.yaml

How to add a new code
=====================

To add a new entry to the ``NWBGitInfo.GIT_REPOS`` dictionary in ``src/nwb_project_analytics/gitstats.py``. The dictionary is used to track all main NWB repositories and stores for each repo a `` GitRepo`` object with basic metadata about the code (e.g., the location of the repo, name of the main branch, etc.). When adding a new code, all statistics need to be updated following the instructions above on **How to update the ``data/``**.

How are code statistcs computed?
================================

The code uses the ``cloc`` tool to calculate line-of-code statistics. Computing ``cloc`` statistics for all codes is time-consuming as we need to compute them over time. This is accomplished by running ``cloc`` for all commits (or more accurately the last commit on each day) on the main branch of each code. The cloc results are saved in the ``data/`` folder to avoid unnecessary updates and safe time.

How to build custom analytics
=============================

The ``nwb_project_analytics`` library includes a number of tools to help
with collecting and plotting data related to NWB code repositories. This includes for example:

* ``nwb_project_analytics.codecovstats`` : Module for getting data from Codecov.io
* ``nwb_project_analytics.codestats`` : Module for computing code statistics using CLOC
* ``nwb_project_analytics.gitstats`` : Module to help query GitHub repos
* ``nwb_project_analytics.renderstats module`` : Module for creating plots for code statistics
* ``nwb_project_analytics.create_codestat_pages`` :  Module used to generate Sphinx documentation with code statistics


