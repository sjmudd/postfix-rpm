#!/bin/sh
#
# $Id: make-postfix.spec,v 1.35.2.14 2002/11/04 10:48:53 sjmudd Exp $
#
# Script to create the postfix.spec file from postfix.spec.in
#
# It's behaviour depends on the version of Red Hat Linux it is running
# on, but this could be extended to other non-redhat distributions.
# 
# The following external variables if set to 1 affect the behaviour
#
# POSTFIX_REDHAT_MYSQL	include support for RedHat's mysql packages
# POSTFIX_REDHAT_DB3	include support for RedHat's db3 packages (rh6.x)
# POSTFIX_MYSQL		include support for MySQL's  MySQL packages
# POSTFIX_LDAP		include support for openldap packages
# POSTFIX_PCRE		include support for pcre maps
# POSTFIX_PGSQL		include support for PostGres database
# POSTFIX_PGSQL2	additional experimental patches provided by
#			George Barbarosie <georgeb@intelinet.ro>
# POSTFIX_SASL		include support for SASL
# POSTFIX_TLS		include support for TLS
# POSTFIX_VDA		include support for Virtual Delivery Agent
# POSTFIX_SMTPD_MULTILINE_GREETING
#			include support for multitline SMTP banner
# POSTFIX_DB4		add support for db4, ignoring db3 (not tested)
# POSTFIX_DISABLE_CHROOT	disable creation of chroot environment
# POSTFIX_RBL_MAPS	LaMont Jones' RBL REPLY Maps patch
# POSTFIX_CDB		support for Constant Database, CDB, by Michael Tokarev
#			<mjt@corpit.ru>, as originally devised by djb.
#
# The following external variables can be used to define the postfix
# uid/gid and postdrop gid if the standard values I'm assigning are
# not correct on your system.
#
# Red Hat Linux 7.x (at the moment) specific requirements
# (This is detected automatically when you rebuild the spec file)
#
# REQUIRES_DB3		add db3 package to requires list
# REQUIRES_INIT_D	add /etc/init.d/ to requires list
# TLSFIX		enable a fix for TLS support on RH 6.2 (see spec file)
#
# To rebuild the spec file, set the appropriate environment
# variables and do the following:
#
# cd `rpm --eval '%{_sourcedir}'`
# export POSTFIX_MYSQL=1	# for example
# sh make-postfix.spec
# cd `rpm --eval '%{_specdir}'`
# rpm -ba postfix.spec

# ensure that these variables are not set from outside
SUFFIX=
REQUIRES_DB3=
REQUIRES_DB4=
REQUIRES_INIT_D=
TLSFIX=
# This appears to be .gz, except for Mandrake 8 which uses .bz2
MANPAGE_SUFFIX=".gz"

echo ""
echo "Creating Postfix spec file: `rpm --eval '%{_specdir}'`/postfix.spec"
echo "  Checking rpm database for distribution information..."
echo "  - if the script gets stuck here:"
echo "    check and remove /var/lib/rpm/__db.00? files"

# Determine the distribution (is there a better way of doing this)

tmpdir=`rpm --eval '%{_sourcedir}'`
distribution=`sh ${tmpdir}/postfix-get-distribution`
releasename=`echo $distribution | sed -e 's;-.*$;;'`
major=`echo $distribution | sed -e 's;[a-z]*-;;' -e 's;\.[0-9]*$;;'`
minor=`echo $distribution | sed -e 's;[a-z]*-;;' -e 's;[0-9]*\.;;'`
echo "  Distribution is: ${distribution}"
echo ""

# Ensure only one of POSTFIX_MYSQL and POSTFIX_REDHAT_MYSQL are defined
[ -n "$POSTFIX_MYSQL" ] && \
[ -n "$POSTFIX_REDHAT_MYSQL" ] && {
    cat <<EOF
Postfix MySQL support
---------------------

There are MySQL packages available from two different sources built with
different package names.  According to the MySQL package you are using
choose to set _ONE_ of the following environment variables accordingly:

POSTFIX_MYSQL = 1	# MySQL packages named MySQL... from www.mysql.com
POSTFIX_REDHAT_MYSQL = 1# MySQL packages named mysql... from RedHat (7+)

Please set the appropriate value and rerun make-postfix.spec again
EOF
    exit 1
}

if [ "$POSTFIX_CDB" = 1 ]; then
    echo "  adding CDB support to spec file"
#   SUFFIX="${SUFFIX}.cdb"
fi

# LDAP support is provided by default on redhat >= 7.2, therefore if
# adding LDAP support on these platforms don't bother to include the .ldap
# suffix. (It is assumed.)
if [ "$POSTFIX_LDAP" = 1 ]; then
    echo "  adding LDAP support to spec file"
    addsuffix=1

    case ${releasename} in
    redhat)
        [ "${major}" -eq 7 -a "${minor}" -ge 2 ] && addsuffix=0
        [ "${major}" -ge 8 ] && addsuffix=0
        ;;
    esac

    [ "$addsuffix" -eq 1 ] && SUFFIX="${SUFFIX}.ldap"
fi
if [ "$POSTFIX_PCRE" = 1 ]; then
    echo "  adding PCRE  support to spec file"
    SUFFIX="${SUFFIX}.pcre"
fi
if [ "$POSTFIX_PGSQL2" = 1 ]; then
    POSTFIX_PGSQL=1
fi
if [ "$POSTFIX_PGSQL" = 1 ]; then
    echo "  adding PostGres support to spec file"
    SUFFIX="${SUFFIX}.pgsql"
fi
if [ "$POSTFIX_PGSQL2" = 1 ]; then
    echo "  including additional experimental PostGres patches"
fi
if [ "$POSTFIX_MYSQL" = 1 ]; then
    POSTFIX_REDHAT_MYSQL=0
    echo "  adding MySQL support (www.mysql.com MySQL* packages) to spec file"
    SUFFIX="${SUFFIX}.MySQL"
fi
if [ "$POSTFIX_REDHAT_MYSQL" = 1 ]; then
    POSTFIX_MYSQL=0
    echo "  adding MySQL support (RedHat mysql* packages) to spec file"
    SUFFIX="${SUFFIX}.mysql"
fi
if [ "$POSTFIX_REDHAT_DB3" = 1 ]; then
    echo "  adding db3 support (RedHat 6.2 db3 packages) to spec file"
    # SUFFIX="${SUFFIX}.db3"
    # we'll change suffix later
fi
if [ "$POSTFIX_SASL" = 1 ]; then
    echo "  adding SASL  support to spec file"
    SUFFIX="${SUFFIX}.sasl"
fi
if [ "$POSTFIX_TLS" = 1 ]; then
    echo "  adding TLS support to spec file"
    SUFFIX="${SUFFIX}.tls"

    if [ ${releasename} = 'redhat' -a ${major} = 6 ]; then
        TLSFIX=1
    fi
fi
if [ "$POSTFIX_VDA" = 1 ]; then
    # don't bother changing the suffix
    echo "  adding VDA support to spec file"
fi
if [ "$POSTFIX_DB4" = 1 ]; then
    echo "  adding db4 support to spec file"
    REQUIRES_DB4=1
fi
if [ "$POSTFIX_DISABLE_CHROOT" = 1 ]; then
    echo "  disabling chroot environment in spec file"
    SUFFIX="${SUFFIX}.nochroot"
fi
if [ "$POSTFIX_RBL_MAPS" = 1 ]; then
    echo "  enabling RBL reply maps patch in spec file"
    SUFFIX="${SUFFIX}.rbl"
fi

# Determine the correct db files to use. RedHat 7 requires db3
# RH6.2 might require db3 if db3-devel is installed
# (db3-devel create a link /lib/libdb.so pointing to /lib/libdb-3.1.so)

case ${releasename} in
redhat)
    case ${major} in
    6)
       if [ "$POSTFIX_REDHAT_DB3" = 1 ]; then
         # we don't test if db3 is installed,
         # just adding db3 to the req and buildreq :
         REQUIRES_DB3=1
         SUFFIX=".db3${SUFFIX}"
       else
         # there will be a problem at link-time if db3-devel is installed
         if  rpm -q db3-devel 2>&1 >/dev/null; then
             echo "   You have the db3-devel package installed. This means that postfix"
             echo "   will be linked againt db3. If you do not want that, uninstall"
             echo "   db3-devel (you don't have to uninstall db3)."
             echo "   If you don't want this message to appear, set"
             echo "   POSTFIX_REDHAT_DB3 to 1 before running $0."
             POSTFIX_REDHAT_DB3=1
             REQUIRES_DB3=1
             SUFFIX=".db3${SUFFIX}"
         fi
       fi
       SUFFIX=".rh6x${SUFFIX}"
       ;;
    7)
	REQUIRES_INIT_D=1
        test -z "$REQUIRES_DB4" && REQUIRES_DB3=1

        case ${minor} in
        0) SUFFIX=".rh70.1${SUFFIX}" ;;
        1) SUFFIX=".rh70.1${SUFFIX}" ;;
        2) ;;
        *) ;;
        esac
        ;;
    *) ;;
    esac
    ;;

mandrake)
    # Mandrake Linux Requirements - This needs some work to be correct.
    #
    # Mandrake 7.1:
    # - db3 is within glibc
    # - the db3 .h files are in glibc-devel
    # Mandrake 8.1
    # - appears to use db3 in the same way as rh7
    case ${major} in
    7) SUFFIX="${SUFFIX}.mdk7x" ;;
    8) test -z "$REQUIRES_DB4" && REQUIRES_DB3=1
       MANPAGE_SUFFIX=".bz2"
       SUFFIX="${SUFFIX}.mdk"
       ;;
    *) SUFFIX="${SUFFIX}.mdk"
    esac
    ;;

*)  ;;
esac

# set default values if they are still undefined

[ -z "$REQUIRES_DB3" ]			   && REQUIRES_DB3=0
[ -z "$REQUIRES_DB4" ]			   && REQUIRES_DB4=0
[ -z "$REQUIRES_INIT_D" ]		   && REQUIRES_INIT_D=0
[ -z "$POSTFIX_LDAP" ]			   && POSTFIX_LDAP=0
[ -z "$POSTFIX_MYSQL" ]			   && POSTFIX_MYSQL=0
[ -z "$POSTFIX_REDHAT_MYSQL" ]		   && POSTFIX_REDHAT_MYSQL=0
[ -z "$POSTFIX_REDHAT_DB3" ]               && POSTFIX_REDHAT_DB3=0
[ -z "$POSTFIX_PCRE" ]			   && POSTFIX_PCRE=0
[ -z "$POSTFIX_PGSQL" ]			   && POSTFIX_PGSQL=0
[ -z "$POSTFIX_PGSQL2" ]		   && POSTFIX_PGSQL2=0
[ -z "$POSTFIX_SASL" ]			   && POSTFIX_SASL=0
[ -z "$POSTFIX_TLS" ]			   && POSTFIX_TLS=0
[ -z "$POSTFIX_VDA" ]			   && POSTFIX_VDA=0
[ -z "$TLSFIX" ]			   && TLSFIX=0
[ -z "$POSTFIX_SMTPD_MULTILINE_GREETING" ] && POSTFIX_SMTPD_MULTILINE_GREETING=0
[ -z "$POSTFIX_DISABLE_CHROOT" ]	   && POSTFIX_DISABLE_CHROOT=0
[ -z "$POSTFIX_RBL_MAPS" ]	           && POSTFIX_RBL_MAPS=0
[ -z "$POSTFIX_CDB" ]	                   && POSTFIX_CDB=0

cat > `rpm --eval '%{_specdir}'`/postfix.spec <<EOF
# W A R N I N G -- DO NOT EDIT THIS FILE -- W A R N I N G
#
# postfix.spec
#
# This file is generated automatically from postfix.spec.in in the SOURCES
# directory.  If you want to build postfix with other options see
# make-postfix.spec in the same directory for instructions.
# --
EOF
sed "
s!__REQUIRES_DB3__!$REQUIRES_DB3!g
s!__REQUIRES_DB4__!$REQUIRES_DB4!g
s!__REQUIRES_INIT_D__!$REQUIRES_INIT_D!g
s!__DISTRIBUTION__!$distribution!g
s!__SMTPD_MULTILINE_GREETING__!$POSTFIX_SMTPD_MULTILINE_GREETING!g
s!__SUFFIX__!$SUFFIX!g
s!__LDAP__!$POSTFIX_LDAP!g
s!__MYSQL__!$POSTFIX_MYSQL!g
s!__REDHAT_MYSQL__!$POSTFIX_REDHAT_MYSQL!g
s!__REDHAT_DB3__!$POSTFIX_REDHAT_DB3!g
s!__PCRE__!$POSTFIX_PCRE!g
s!__PGSQL__!$POSTFIX_PGSQL!g
s!__PGSQL2__!$POSTFIX_PGSQL2!g
s!__SASL__!$POSTFIX_SASL!g
s!__TLS__!$POSTFIX_TLS!g
s!__TLSFIX__!$TLSFIX!g
s!__VDA__!$POSTFIX_VDA!g
s!__DISABLE_CHROOT__!$POSTFIX_DISABLE_CHROOT!g
s!__RBL_MAPS__!$POSTFIX_RBL_MAPS!g
s!__CDB__!$POSTFIX_CDB!g
s!__MANPAGE_SUFFIX__!$MANPAGE_SUFFIX!g
" `rpm --eval '%{_sourcedir}'`/postfix.spec.in >> `rpm --eval '%{_specdir}'`/postfix.spec

# end of make-postfix.spec
