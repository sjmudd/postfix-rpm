

# help
help:
	cat <<END
This is a help file

Makefile targets are:

help	this help file
commit	commit changes to cvs repository
checkcvs	check if there are changes which have not been added to the repository
tidy		clean up the BUILD and tmp directorys and remove links in SOURCES directory
rpm		build the rpm
copyover	copy over the built rpm to the main machine
tests		various test for the optional patches
END

# Build the rpm
default: rpm

# commit changes to cvs
commit:
	@cvs diff 2>/dev/null >/dev/null || cvs commit

# checks if there have been changes to source
checkcvs:

# remove stuff in BUILDDIR, remove links in SOURCES, remove files in tmp directory
tidy:

# build the rpm
rpm:
	@echo Building RPM
	@sh buildpackage

# Tests - test the different patches
tests: vda_test


# Test the rpm prep stage for VDA patches - do they apply cleanly?
vda_test:
    specdir=rpm --eval '%{_specdir}'
    [ "${test_vda}" = 1 ] && {
    @echo ""
    @echo "===> testing VDA patches"
    ( cd ${srcdir} && \
      POSTFIX_VDA=1 sh make-postfix.spec && \
      cd ${specdir} && \
      rpmbuild -bp postfix.spec ) || { echo "===> testing VDA patches: ** FAILED **"; exit 1; }
      echo "===> testing VDA patches: ** OK **"
      echo ""
    }
