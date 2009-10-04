#
# Makefile for producing my Postfix RPMs
#

all: setup update fetch build

# Setup the directory structure used (on a non-root machine)
# normally done just once after checking out the repository
# files.
setup:
	@echo "--------------------------------------------------------------"
	@echo ">>> Setting up directory structure"
	@echo "--------------------------------------------------------------"
	@echo ""
	@sh setup-rpm-environment

# update to the latest version of the rpm
# (no longer builds)
update latest:
	@echo "--------------------------------------------------------------"
	@echo ">>> updating files from git repo"
	@echo "--------------------------------------------------------------"
	@echo ""
	@git pull || : 

# download files if necessary
fetch:
	@echo "--------------------------------------------------------------"
	@echo ">>> downloading source files (if needed)"
	@echo "--------------------------------------------------------------"
	@echo ""
	@LANG= LC_CTYPE= LANG= ./vcheck --plain --no-update --download --catch-up --file postfix.spec.vc

# build the rpm
build rpm:
	@echo "--------------------------------------------------------------"
	@echo ">>> Building RPM"
	@echo "--------------------------------------------------------------"
	@echo ""
	@sh buildpackage

# build the rpm with no cvs checks first
nochecks:
	@echo "--------------------------------------------------------------"
	@echo ">>> Building RPM (no cvs checks)"
	@echo "--------------------------------------------------------------"
	@echo ""
	@sh buildpackage --no-check

# Build the rpm
default: rpm 

# commit changes to cvs
commit:
	@cvs commit

# checks if there have been changes to source
checkcvs:
	@echo ""
	@echo "--------------------------------------------------------------"
	@echo ">>> Checking for changes against the CVS repository"
	@echo "--------------------------------------------------------------"
	@echo ""
	@cvs diff 2>&1 >/dev/null || { echo ""; echo "WARNING Commit changes before building, or try $(MAKE) nochecks"; exit 1; }


# Tests - test the different patches
tests:
	@echo "--------------------------------------------------------------"
	@echo ">>> testing patches"
	@echo "--------------------------------------------------------------"
	@echo ""
	@sh test-patches

# clean up the directory structure of files which we don't need
# - links from this package into SOURCES
# - any other symbolic links in %{_sourcedir} ~user/rpm/SOURCES
# - stuff in %{_tmppath} ~user/rpm/tmp/*
# - stuff in %{_builddir} ~user/rpm/BUILD/*
clean tidy:
	@sh linkfiles --delete --quiet || :
	@dir=`rpm --eval '%{_sourcedir}' | sed 's;%{name};postfix;'` ; \
		for file in `ls $$dir`; do [ -L $$file ] && rm $$file || :; done
	@dir=`/bin/rpm --eval '%{_sourcedir}'`; \
		dir=`rpm --eval '%{_tmppath}'  | sed 's;%{name};postfix;'`; \
		[ -d $$dir ] && rm -rf $$dir/* || :
	@dir=`rpm --eval '%{_builddir}' | sed 's;%{name};postfix;'`; \
		[ -d $$dir ] && rm -rf $$dir/* || :
	@[ -e postfix-build.log ] && rm postfix-build.log || :
	@for file in `ls results.* 2>/dev/null`; do rm $$file || :; done

# Give some help
help:
	@[ -f README ] && more README || echo "No help available sorry"
