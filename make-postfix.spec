#!/bin/sh
#
# $Id: make-postfix.spec,v 1.35.2.2 2002/01/19 10:04:06 sjmudd Exp $
#
# Script to create the postfix.spec file from postfix.spec.in
#
# It's behaviour depends on the version of Red Hat Linux it is running
# on, but this could be extended to other non-redhat distributions.
# 
# The following external variables if set to 1 affect the behaviour
#
# POSTFIX_REDHAT_MYSQL	include support for RedHat's mysql packages
# POSTFIX_MYSQL		include support for MySQL's  MySQL packages
# POSTFIX_LDAP		include support for openldap packages
# POSTFIX_PCRE		include support for pcre maps
# POSTFIX_SASL		include support for SASL
# POSTFIX_TLS		include support for TLS
# POSTFIX_SMTPD_MULTILINE_GREETING
#			include support for multitline SMTP banner
#
# The following external variable can be used to define the postdrop
# gid if the standard value I'm assigning is not correct on your system.
#
# POSTFIX_POSTDROP_GID  (default value 90)
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
REQUIRES_INIT_D=
TLSFIX=

echo ""
echo "Creating Postfix spec file: `rpm --eval '%{_specdir}'`/postfix.spec"
echo "  Checking rpm database for distribution information..."
echo "  - if the script gets stuck here:"
echo "    check and remove /var/lib/rpm/__db.00? files"

# Determine the distribution (is there a better way of doing this)
DISTRIBUTION=`rpm -qa | grep -- -release | egrep '(redhat-|mandrake-)'`
[ -z "$DISTRIBUTION" ] && DISTRIBUTION='Unknown Distribution'

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

# Get release information (if possible)
if [ `rpm -q redhat-release >/dev/null 2>&1; echo $?` = 0 ]; then
    releasename=redhat
    release=`rpm -q redhat-release | sed -e 's;^redhat-release-;;' -e 's;-[0-9]*$;;'`
elif [ `rpm -q mandrake-release >/dev/null 2>&1; echo $?` = 0 ]; then
    releasename=mandrake
    release=`rpm -q mandrake-release | sed -e 's;^mandrake-release-;;' -e 's;-[0-9]*mdk$;;'`
else
    releasename=unknown
    release=0.0
fi
major=`echo $release | sed -e 's;\.[0-9]*$;;'`
minor=`echo $release | sed -e 's;^[0-9]*\.;;'`

echo "  Distribution is: ${releasename} ${major}.${minor}"
echo ""

if [ "$POSTFIX_LDAP" = 1 ]; then
    echo "  adding LDAP  support to spec file"
    SUFFIX="${SUFFIX}.ldap"
fi
if [ "$POSTFIX_PCRE" = 1 ]; then
    echo "  adding PCRE  support to spec file"
    SUFFIX="${SUFFIX}.pcre"
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

# Determine the correct db files to use. RedHat 7 requires db3
case ${releasename} in
redhat)
    case ${major} in
    6) SUFFIX=".rh6x${SUFFIX}" ;;
    7)
	REQUIRES_INIT_D=1
        REQUIRES_DB3=1

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
    7) SUFFIX="${SUFFIX}mdk7x" ;;
    8) REQUIRES_DB3=1
       SUFFIX="${SUFFIX}mdk"
       ;;
    *) SUFFIX="${SUFFIX}mdk"
    esac
    ;;

*)  ;;
esac

# set default values if they are still undefined

[ -z "$REQUIRES_DB3" ]			   && REQUIRES_DB3=0
[ -z "$REQUIRES_INIT_D" ]		   && REQUIRES_INIT_D=0
[ -z "$POSTFIX_LDAP" ]			   && POSTFIX_LDAP=0
[ -z "$POSTFIX_MYSQL" ]			   && POSTFIX_MYSQL=0
[ -z "$POSTFIX_REDHAT_MYSQL" ]		   && POSTFIX_REDHAT_MYSQL=0
[ -z "$POSTFIX_PCRE" ]			   && POSTFIX_PCRE=0
[ -z "$POSTFIX_SASL" ]			   && POSTFIX_SASL=0
[ -z "$POSTFIX_TLS" ]			   && POSTFIX_TLS=0
[ -z "$TLSFIX" ]			   && TLSFIX=0
[ -z "$POSTFIX_SMTPD_MULTILINE_GREETING" ] && POSTFIX_SMTPD_MULTILINE_GREETING=0
[ -z "$POSTFIX_POSTDROP_GID" ]             && POSTFIX_POSTDROP_GID=90

cat > `rpm --eval '%{_specdir}'`/postfix.spec <<EOF
##############################################################################
#
# W A R N I N G -- DO NOT EDIT THIS FILE -- W A R N I N G
#
# It is generated automatically from postfix.spec.in in the SOURCES directory.
#
# See make-postfix.spec for instructions on rebuilding on a different
# distribution or with different options.
#
# W A R N I N G -- DO NOT EDIT THIS FILE -- W A R N I N G
#
EOF
sed "
s!__REQUIRES_DB3__!$REQUIRES_DB3!g
s!__REQUIRES_INIT_D__!$REQUIRES_INIT_D!g
s!__DISTRIBUTION__!$DISTRIBUTION!g
s!__SMTPD_MULTILINE_GREETING__!$POSTFIX_SMTPD_MULTILINE_GREETING!g
s!__SUFFIX__!$SUFFIX!g
s!__LDAP__!$POSTFIX_LDAP!g
s!__MYSQL__!$POSTFIX_MYSQL!g
s!__REDHAT_MYSQL__!$POSTFIX_REDHAT_MYSQL!g
s!__PCRE__!$POSTFIX_PCRE!g
s!__SASL__!$POSTFIX_SASL!g
s!__TLS__!$POSTFIX_TLS!g
s!__TLSFIX__!$TLSFIX!g
s!__POSTDROP_GID__!$POSTFIX_POSTDROP_GID!g
" postfix.spec.in >> `rpm --eval '%{_specdir}'`/postfix.spec

# end of make-postfix.spec
