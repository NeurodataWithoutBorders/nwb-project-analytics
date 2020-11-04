=====================
nwb-project-analytics
=====================

Repository for collecting analytics and scripts related to the NWB project. 

Software Health
===============

Latest Releases
---------------

.. table::

 +------------+-----------------------------------------------------------------------------------------+-----------------------------------------------------------------------------------------+-----------------------------------------------------------------------------------------+
 |            | **PyNWB**                                                                               | **HDMF**                                                                                | **HDMF Docutils**                                                                       |
 +============+=========================================================================================+=========================================================================================+=========================================================================================+
 | **PyPi**   | .. image:: https://badge.fury.io/py/pynwb.svg                                           |  .. image:: https://badge.fury.io/py/hdmf.svg                                           | .. image:: https://badge.fury.io/py/hdmf-docutils.svg                                   |
 |            |     :target: https://badge.fury.io/py/pynwb                                             |      :target: https://badge.fury.io/py/hdmf                                             |      :target: https://badge.fury.io/py/hdmf-docutils                                    |
 |            |     :alt:    PyPI - Verion                                                              |      :alt:    PyPI - Version                                                            |      :alt:    PyPI - Version                                                            |
 +------------+-----------------------------------------------------------------------------------------+-----------------------------------------------------------------------------------------+-----------------------------------------------------------------------------------------+
 | **Conda**  | .. image:: https://anaconda.org/conda-forge/pynwb/badges/version.svg                    |  .. image:: https://anaconda.org/conda-forge/hdmf/badges/version.svg                    |                                                                                         |
 |            |     :target: https://anaconda.org/conda-forge/pynwb                                     |      :target: https://anaconda.org/conda-forge/hdmf                                     |                                                                                         |
 |            |     :alt:    Conda - Version                                                            |      :alt:    Conda - Version                                                           |                                                                                         |
 +------------+-----------------------------------------------------------------------------------------+-----------------------------------------------------------------------------------------+-----------------------------------------------------------------------------------------+
 
.. table::

  +-------------------+--------------------------------------------------------------------------------------------------------+
  |                   | **MatNWB**                                                                                             |
  +===================+========================================================================================================+
  | **File Exchange** | .. image:: https://www.mathworks.com/matlabcentral/images/matlab-file-exchange.svg                     |
  |                   |     :target: https://www.mathworks.com/matlabcentral/fileexchange/67741-neurodatawithoutborders-matnwb |
  |                   |     :alt: MathWorks FileExchange                                                                       |
  +-------------------+--------------------------------------------------------------------------------------------------------+


Licences
--------

.. table::

 +-----------------------------------------------------------------------------------------+-----------------------------------------------------------------------------------------+-----------------------------------------------------------------------------------------+
 | **PyNWB**                                                                               | **HDMF**                                                                                | **HDMF Docutils**                                                                       |
 +=========================================================================================+=========================================================================================+=========================================================================================+
 | .. image:: https://img.shields.io/pypi/l/pynwb.svg                                      |  .. image:: https://img.shields.io/pypi/l/hdmf.svg                                      | .. image:: https://img.shields.io/pypi/l/hdmf-docutils.svg                              |
 |     :target: https://github.com/neurodatawithoutborders/pynwb/blob/dev/license.txt      |      :target: https://github.com/hdmf-dev/hdmf/blob/master/license.txt                  |      :target: https://github.com/hdmf-dev/hdmf-docutils/blob/master/license.txt         |
 |     :alt:    PyPI - License                                                             |      :alt:    PyPI - License                                                            |      :alt:    PyPI - License                                                            |
 +-----------------------------------------------------------------------------------------+-----------------------------------------------------------------------------------------+-----------------------------------------------------------------------------------------+


Build Status
------------

.. table::

  +-------------+--------------------------------------------------------------------------------------------------------------------------------+------------------------------------------------------------------------------------------------+---------------+
  |             | **PyNWB**                                                                                                                      | **HDMF**                                                                                       | HDMF DocUtils |
  +=============+================================================================================================================================+================================================================================================+===============+
  | **Linux**   | .. image:: https://circleci.com/gh/NeurodataWithoutBorders/pynwb.svg?style=shield                                              | .. image:: https://circleci.com/gh/hdmf-dev/hdmf.svg?style=shield                              | Not tested    |
  |             |      :target: https://circleci.com/gh/NeurodataWithoutBorders/pynwb                                                            |      :target: https://circleci.com/gh/hdmf-dev/hdmf                                            |               |
  |             |      :alt: CircleCI Status                                                                                                     |      :alt: CircleCI Status                                                                     |               |
  +-------------+--------------------------------------------------------------------------------------------------------------------------------+------------------------------------------------------------------------------------------------+---------------+
  | **Windows** | .. image:: https://dev.azure.com/NeurodataWithoutBorders/pynwb/_apis/build/status/NeurodataWithoutBorders.pynwb?branchName=dev | .. image:: https://dev.azure.com/hdmf-dev/hdmf/_apis/build/status/hdmf-dev.hdmf?branchName=dev | Not testet    |
  |             |      :target: https://dev.azure.com/NeurodataWithoutBorders/pynwb/_build/latest?definitionId=3&branchName=dev                  |     :target: https://dev.azure.com/hdmf-dev/hdmf/_build/latest?definitionId=1&branchName=dev   |               |
  |             |      :alt: Azure Status                                                                                                        |     :alt: Azure Status                                                                         |               |
  +-------------+--------------------------------------------------------------------------------------------------------------------------------+------------------------------------------------------------------------------------------------+---------------+
  | **MacOS**   | .. image:: https://dev.azure.com/NeurodataWithoutBorders/pynwb/_apis/build/status/NeurodataWithoutBorders.pynwb?branchName=dev | .. image:: https://dev.azure.com/hdmf-dev/hdmf/_apis/build/status/hdmf-dev.hdmf?branchName=dev | Not tested    |
  |             |      :target: https://dev.azure.com/NeurodataWithoutBorders/pynwb/_build/latest?definitionId=3&branchName=dev                  |     :target: https://dev.azure.com/hdmf-dev/hdmf/_build/latest?definitionId=1&branchName=dev   |               |
  |             |      :alt: Azure Status                                                                                                        |     :alt: Azure Status                                                                         |               |
  +-------------+--------------------------------------------------------------------------------------------------------------------------------+------------------------------------------------------------------------------------------------+---------------+
  | **Conda**   | .. image:: https://circleci.com/gh/conda-forge/pynwb-feedstock.svg?style=shield                                                | .. image:: https://circleci.com/gh/conda-forge/hdmf-feedstock.svg?style=shield                 | Not tested    |
  |             |       :target: https://circleci.com/gh/conda-forge/pynwb-feedstocks                                                            |     :target: https://circleci.com/gh/conda-forge/hdmf-feedstock                                |               |
  |             |       :alt: Conda Feedstock Status                                                                                             |     :alt: Conda Feedstock Status                                                               |               |
  |             |                                                                                                                                |                                                                                                |               |
  +-------------+--------------------------------------------------------------------------------------------------------------------------------+------------------------------------------------------------------------------------------------+---------------+

Overall Health
--------------

.. table::

  +-------------------+-------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------+--------------------------------------------------------------------------------------+----------------------------------------------------------------------------------------+-------------------+
  |                   | **PyNWB**                                                                                       | **HDMF**                                                                        | **HDMF Common Schema**                                                               | **HDMF Schema Language**                                                               | **HDMF Docutils** |
  +===================+=================================================================================================+=================================================================================+======================================================================================+========================================================================================+===================+
  | **Coverage**      | .. image:: https://codecov.io/gh/NeurodataWithoutBorders/pynwb/branch/dev/graph/badge.svg       | .. image:: https://codecov.io/gh/hdmf-dev/hdmf/branch/dev/graph/badge.svg       | N/A                                                                                  | N/A                                                                                    | Missing           |
  |                   |     :target: https://codecov.io/gh/NeurodataWithoutBorders/pynwb                                |     :target: https://codecov.io/gh/hdmf-dev/hdmf    :alt: Code Coverage         |                                                                                      |                                                                                        |                   |
  |                   |     :alt: Code Coverage                                                                         |                                                                                 |                                                                                      |                                                                                        |                   |
  +-------------------+-------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------+--------------------------------------------------------------------------------------+----------------------------------------------------------------------------------------+-------------------+
  | **Requirements**  | .. image:: https://requires.io/github/NeurodataWithoutBorders/pynwb/requirements.svg?branch=dev | .. image:: https://requires.io/github/hdmf-dev/hdmf/requirements.svg?branch=dev | N/A                                                                                  | N/A                                                                                    | Missing           |
  |                   |      :target: https://requires.io/github/NeurodataWithoutBorders/pynwb/requirements/?branch=dev |      :target: https://requires.io/github/hdmf-dev/hdmf/requirements/?branch=dev |                                                                                      |                                                                                        |                   |
  |                   |      :alt: Requirements Status                                                                  |      :alt: Requirements Status                                                  |                                                                                      |                                                                                        |                   |
  +-------------------+-------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------+--------------------------------------------------------------------------------------+----------------------------------------------------------------------------------------+-------------------+
  | **Documentation** | .. image:: https://readthedocs.org/projects/pynwb/badge/?version=latest                         | .. image:: https://readthedocs.org/projects/hdmf/badge/?version=latest          | .. image:: https://readthedocs.org/projects/hdmf-common-schema/badge/?version=latest | .. image:: https://readthedocs.org/projects/hdmf-schema-language/badge/?version=latest | Missing           |
  |                   |      :target: https://pynwb.readthedocs.io/en/latest/?badge=latest                              |      :target: https://hdmf.readthedocs.io/en/latest/?badge=latest               |      :target: https://hdmf-common-schema.readthedocs.io/en/latest/?badge=latest      |      :target: https://hdmf-schema-language.readthedocs.io/en/latest/?badge=latest      |                   |
  |                   |      :alt: Documentation Status                                                                 |      :alt: Documentation Status                                                 |      :alt: Documentation Status                                                      |      :alt: Documentation Status                                                        |                   |
  +-------------------+-------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------+--------------------------------------------------------------------------------------+----------------------------------------------------------------------------------------+-------------------+
