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

# Update to the latest version of the rpm
# (no longer builds)
update latest:
	@echo "--------------------------------------------------------------"
	@echo ">>> updating local files from remote git repository"
	@echo "--------------------------------------------------------------"
	@echo ""
	@git pull || : 

# Build the .vc file as vcheck doesn't allow parameters and we need to
# add %{_sourcedir}
postfix.spec.vc: postfix.spec.vc.in
	@srcdir=`/bin/rpm --eval '%{_sourcedir}'`; \
		sed -e "s;@@SRCDIR@@;$$srcdir;" -e 's;%{name};postfix;' $< > $@

# Download files if necessary
fetch: postfix.spec.vc
	@echo "--------------------------------------------------------------"
	@echo ">>> downloading source files (if needed)"
	@echo "--------------------------------------------------------------"
	@echo ""
	@LANG= LC_CTYPE= LANG= ./vcheck --plain --no-update --download --catch-up --file postfix.spec.vc

# build the rpm
build rpm:
	@echo '--------------------------------------------------------------'
	@echo '>>> Building RPM and signing if necessary'
	@echo '--------------------------------------------------------------'
	@echo ''
	@if grep -q '^%_signature' ~/.rpmmacros && grep -q '^%_gpg_name' ~/.rpmmacros && grep -q '^%_gpg_path' ~/.rpmmacros; then sign=''; else sign='--no-sign'; fi; \
		sh buildpackage $$sign

# build the rpm with no checks for locally uncommitted changes.
nochecks:
	@echo "--------------------------------------------------------------"
	@echo ">>> Building RPM (no git checks)"
	@echo "--------------------------------------------------------------"
	@echo ""
	@sh buildpackage --no-check

# Build the rpm
default: rpm 

# commit changes to git - probably should NOT be doing this...
commit:
	@git commit "Commit local changes from Makefile"

# checks if there have been changes to source
checkgit:
	@echo ""
	@echo "--------------------------------------------------------------"
	@echo ">>> Checking for local changes against the git repository"
	@echo "--------------------------------------------------------------"
	@echo ""
	@git diff 2>&1 >/dev/null || { echo ""; echo "WARNING Commit changes before building, or try $(MAKE) nochecks"; exit 1; }

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
	@for f in postfix.spec.vc postfix-build.log; do [ -e $$f ] && rm $$f || :; done
	@sh linkfiles --delete --quiet || :
	@dir=`rpm --eval '%{_sourcedir}' | sed 's;%{name};postfix;'` ; \
		for file in `ls $$dir`; do [ -L $$file ] && rm $$file || :; done
	@dir=`/bin/rpm --eval '%{_sourcedir}'`; \
		dir=`rpm --eval '%{_tmppath}'  | sed 's;%{name};postfix;'`; \
		[ -d $$dir ] && rm -rf $$dir/* || :
	@dir=`rpm --eval '%{_builddir}' | sed 's;%{name};postfix;'`; \
		[ -d $$dir ] && rm -rf $$dir/* || :
	@for file in `ls results.* 2>/dev/null`; do rm $$file || :; done

# Give some help
help:
	@[ -f README ] && more README || echo "No help available sorry"
