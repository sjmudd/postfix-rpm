#
# Makefile for producing my Postfix RPMs
#

# Setup the directory structure used (on a non-root machine)
# normally done just once after checking out the repository
# files.
setup:
	@echo Setting up directory structure
	@sh setup-rpm-environment

# Build the rpm
default: rpm 

# commit changes to cvs
commit:
	@cvs commit

# checks if there have been changes to source
checkcvs:
	@cvs diff

# update to the latest version of the rpm
# (no longer builds)
update latest:
	@echo updating CVS files
	@cvs update || : 

# build the rpm
rpm:
	@echo Building RPM; \
	sh buildpackage

# Tests - test the different patches
tests: vda_test


# Test the rpm prep stage for VDA patches - do they apply cleanly?
vda-test:
	@echo ""
	@echo "===> testing VDA patches"
	@specdir=$(rpm --eval '%{_specdir}' | sed 's;%{name};postfix;'); \
	srcdir=$(rpm --eval '%{_sourcedir}' | sed 's;%{name};postfix;'); \
	( cd $$srcdir && \
	  pwd && \
	POSTFIX_VDA=1 sh make-postfix.spec && \
	cd $$specdir && \
	rpmbuild -bp postfix.spec ) || { echo "===> testing VDA patches: ** FAILED **"; exit 1; }

#	echo "===> testing VDA patches: ** OK **"
#	echo ""

# clean up the directory structure of files which we don't need
# - links from this package into SOURCES
# - any other symbolic links in %{_sourcedir} ~user/rpm/SOURCES
# - stuff in %{_tmppath} ~user/rpm/tmp/*
# - stuff in %{_builddir} ~user/rpm/BUILD/*
clean tidy:
	sh linkfiles --delete --quiet || :
	dir=$(rpm --eval '%{_sourcedir}' | sed 's;%{name};postfix;')
	for i in `ls $$dir`; do [ -L $$i ] && rm $$i || :; done
	dir=$(rpm --eval '%{_tmppath}'); rm -rf $$dir/*
	dir=$(rpm --eval '%{_builddir}'); rm -rf $$dir/*
	[ -e build-output ] && rm build-output || :

# Give some help
help:
	@[ -f README ] && more README || echo "No help available sorry"
