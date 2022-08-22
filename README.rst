=====================
nwb-project-analytics
=====================

Repository for collecting analytics and scripts related to the NWB project.

The NWB project maintains and contributes to a large number of codes
related to NWB. The goal of this effort is to help  developers to get a
quick overview of the state of NWB code repositories. See, e.g., the `code health page <https://github.com/NeurodataWithoutBorders/nwb-project-analytics/blob/main/docs/source/code_health.rst>`_

How to use nwb-project-analytics (the docs)
===========================================

All main NWB analytics are compiled automatically when building the ``docs``

1. Create a virtual enf (option)

.. code-block:: bash:

    conda create --name nwb_analytics_env python=3.8
    conda activate nwb_analytics_env

2. Install ``cloc`` (see `here <https://github.com/AlDanial/cloc#install-via-package-manager>`_)

3. Install the tools via

.. code-block:: bash

    git clone https://github.com/NeurodataWithoutBorders/nwb-project-analytics.git
    cd nwb-project-analytics
    pip install -r requirements.txt -r requirements-doc.txt
    pip install -e .

4. Build the docs

.. code-block:: bash

    cd docs
    make html
    open build/html/index.html


How to update the ``data/``
===========================

Computing ``cloc`` statistics for all codes is time-consuming as we need to compute them over time, i.e., we need to run ``cloc`` for all commits on the main branch of each code. The cloc results are, therefore, saved in the ``data/`` folder and only updated when necessary. To update the ``cloc`` statistics simply remove the cached results and build the docs:

.. code-block:: bash

    rm data/cloc_stats.yaml
    rm data/commit_stats.yaml
    rm data/git_path.yaml
    cd docs
    make html

How to build custom analytics
=============================

The ``nwb_project_analytics`` library includes a number of tools to help
with collecting and plotting data related to NWB code repositories. This includes for example:

* ``nwb_project_analytics.codecovstats`` : Module for getting data from Codecov.io
* ``nwb_project_analytics.codestats`` : Module for computing code statistics using CLOC
* ``nwb_project_analytics.gitstats`` : Module to help query GitHub repos
* ``nwb_project_analytics.renderstats module`` : Module for creating plots for code statistics
* ``nwb_project_analytics.create_codestat_pages`` :  Module used to generate Sphinx documentation with code statistics


