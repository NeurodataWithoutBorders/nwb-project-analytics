# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = source
BUILDDIR      = build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	@echo "\033[0;34m  allclean\033[0m    to remove all auto-generated source files and everything in the build directory"

.PHONY: help Makefile

# All clean
allclean:
	@echo "Removing auto-generated code statistic pages in 'source/code_stat_pages' ..."
	@rm -rf source/code_stat_pages
	@echo "Removing auto-generated apidoc RST files 'source/nwb_project_analytics.*rst' ..."
	@rm -f source/nwb_project_analytics.*rst
	@make clean

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
