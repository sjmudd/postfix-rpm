#!/bin/sh
#
# $Id: make-postfix.spec,v 2.22.2.6 2004/12/08 18:39:24 sjmudd Exp $
#
# Script to create the postfix.spec file from postfix.spec.in
#
# It's behaviour depends on the version of Red Hat Linux it is running
# on, but this could be extended to other non-redhat distributions.
# 
# The following external variables if set to 1 affect the behaviour
#
# POSTFIX_CDB		support for Constant Database, CDB, by Michael Tokarev
#			<mjt@corpit.ru>, as originally devised by djb.
# POSTFIX_IPV6		include support for IPv6
# POSTFIX_LDAP		include support for openldap packages
# POSTFIX_MYSQL		include support for MySQL's MySQL packages
# POSTFIX_MYSQL_REDHAT	include support for RedHat's mysql packages
# POSTFIX_MYSQL_PATHS	include support for locally installed mysql binary,
#			providing the colon seperated include and
#			library paths ( /usr/include/mysql:/usr/lib/mysql )
# POSTFIX_MYSQL_QUERY	include support for writing full select statements
#			in mysql maps
# POSTFIX_PCRE		include support for pcre maps
# POSTFIX_PGSQL		include support for PostGres database
# POSTFIX_SASL		include support for SASL (1, 2 or 0 to disable)
# POSTFIX_SMTPD_MULTILINE_GREETING
#			include support for multitline SMTP banner
# POSTFIX_SPF           include support for libspf2
# POSTFIX_TLS		include support for TLS
# POSTFIX_VDA		include support for Virtual Delivery Agent
#
# These two values will be setup according to your distribution, but
# you may override them.
# POSTFIX_DB		add support for dbX, (3, 4, or 0 to disable)
#
# Distribution Specific Configurations
# ------------------------------------
#
# Please advise me if any of these assumptions are incorrect.
#
# REQUIRES_ZLIB		0 by default, 1 when used with TLS on RH9 & RHEL3
#			              1 when used with mysql_redhat/mysql
#
# All Red Hat Enterprise Linuxes will now be treated identically
# and named rhelXX
# - LDAP support is included on all enterprise linux varieties
#
# POSTFIX_DB=4		add db4 package to requires list
# - Red Hat Linux Enterprise 3
# - Red Hat Linux 9
# - Red Hat Linux 8
#
# POSTFIX_DB=3		add db3 package to requires list
# - Red Hat Linux Enterprise 2.1
# - Red Hat Linux 7.x
#
# Red Hat Linux MAY require (according to configuration)
# TLSFIX=1		enable a fix for TLS support on RH 6.2 (see spec file)
# TLSFIX=2		enable a fix for TLS support on RH 9 and RHEL3
#
# For build instructions see:
# - postfix.spec[.in]	if you have the source rpm installed
# - postfix.spec.cf	if you have the binary rpm installed

[ -n "$DEBUG" ] && set -x
myname=`basename $0`

error() {
    echo "$myname: Error;$1" >&2; exit 1
}

# ensure that these variables are NOT set from outside and complain if they
# are.

[ `set | grep ^SUFFIX= | wc -l`          = 0 ] || error "Please do not set SUFFIX"
[ `set | grep ^TLSFIX= | wc -l`          = 0 ] || error "Please do not set TLSFIX"

SUFFIX=			# RPM package suffix
TLSFIX=			# Apply "fixes" to TLS patches

# change location of spec/source dir so they can be referenced by "%{name}"
specdir=$(rpm --eval '%{_specdir}' | sed 's;%{name};postfix;')
sourcedir=$(rpm --eval '%{_sourcedir}' | sed 's;%{name};postfix;')

echo ""
echo "Creating Postfix spec file: ${specdir}/postfix.spec"
echo "  Checking rpm database for distribution information..."
echo "  - if the script gets stuck here:"
echo "    check and remove /var/lib/rpm/__db.00? files"

# Determine the distribution (is there a better way of doing this?)
# - give (example values as shown)
#
# redhat-release-9.0-3 | whitebox-release-3.0-6_i386
# redhat-9.0           | rhel-3.0
# redhat               | rhel
# 9                    | 3
# 0                    | 0

fullname=`sh ${sourcedir}/postfix-get-distribution --full`
distribution=`sh ${sourcedir}/postfix-get-distribution`
releasename=`sh ${sourcedir}/postfix-get-distribution --name`
major=`sh ${sourcedir}/postfix-get-distribution --major`
minor=`sh ${sourcedir}/postfix-get-distribution --minor`

echo "  Distribution is: ${fullname} (${distribution})"
echo ""

if [ "$POSTFIX_CDB" = 1 ]; then
    echo "  adding CDB support to spec file"
    SUFFIX="${SUFFIX}.cdb"
fi

# --- POSTFIX_LDAP --- do we require openldap support?
#
# LDAP support is included by default: except
#	redhat < 7.2
#	rhel < 2.1
#	yellowdog < 2.3.

DEFAULT_LDAP=1
case ${releasename} in
redhat)
    [ "${major}" -eq 7 -a "${minor}" -lt 2 ] && DEFAULT_LDAP=0
    [ "${major}" -le 6 ] && DEFAULT_LDAP=0
    ;;

rhel)
    [ "${major}" -eq 2 -a "${minor}" -lt 1 ] && DEFAULT_LDAP=0
    [ "${major}" -le 1 ] && DEFAULT_LDAP=0
    ;;

yellowdog)
    [ "${major}" -eq 2 -a "${minor}" -lt 3 ] && DEFAULT_LDAP=0
    [ "${major}" -le 1 ] && DEFAULT_LDAP=0
    ;;
esac

test -z "${POSTFIX_LDAP}" && POSTFIX_LDAP=${DEFAULT_LDAP}
if [ "${POSTFIX_LDAP}" = 1 ]; then
    echo "  adding LDAP support to spec file"

    # Only add the .ldap suffix if the distribution by default doesn´t support ldap
    [ "${POSTFIX_LDAP}" != "${DEFAULT_LDAP}" ] && SUFFIX="${SUFFIX}.ldap"
fi

if [ "$POSTFIX_PCRE" = 1 ]; then
    echo "  adding PCRE support to spec file"
    SUFFIX="${SUFFIX}.pcre"
fi
if [ "$POSTFIX_PGSQL" = 1 ]; then
    echo "  adding PostGres support to spec file"
    SUFFIX="${SUFFIX}.pgsql"
fi
# Check for conflicting MySQL requests and report an error if necessary
MYSQL_COUNT=0
[ -n "$POSTFIX_MYSQL"        -a "$POSTFIX_MYSQL"        != 0 ] && MYSQL_COUNT=$(($MYSQL_COUNT + 1))
[ -n "$POSTFIX_MYSQL_REDHAT" -a "$POSTFIX_MYSQL_REDHAT" != 0 ] && MYSQL_COUNT=$(($MYSQL_COUNT + 1))
[ -n "$POSTFIX_MYSQL_PATHS"                                ] && MYSQL_COUNT=$(($MYSQL_COUNT + 1))
[ ${MYSQL_COUNT} -gt 1 ] && {
        cat <<-END
	ERROR: You can only set ONE of the following:
	  POSTFIX_MYSQL_REDHAT (use RedHat built MySQL packages)
	  POSTFIX_MYSQL	       (use MySQL built MySQL packages)
	  POSTFIX_MYSQL_PATHS  (provide paths to include and library directories
	                        for manually installed MySQL server)
	  Select the variable you want and unset the other ones.
	END
	exit 1
}
if [ "$POSTFIX_MYSQL" = 1 ]; then
    POSTFIX_MYSQL_REDHAT=0
    POSTFIX_MYSQL_PATHS=
    echo "  adding MySQL support (www.mysql.com MySQL* packages) to spec file"
    SUFFIX="${SUFFIX}.MySQL"
fi
if [ -n "$POSTFIX_REDHAT_MYSQL" ]; then
    cat <<END
WARNING: POSTFIX_REDHAT_MYSQL has been replaced by POSTFIX_MYSQL_REDHAT.
  Please unset POSTFIX_REDHAT_MYSQL and set POSTFIX_MYSQL_REDHAT to continue.
END
    exit 1
fi
if [ "$POSTFIX_MYSQL_REDHAT" = 1 ]; then
    POSTFIX_MYSQL=0
    POSTFIX_MYSQL_PATHS=
    echo "  adding MySQL support (RedHat mysql* packages) to spec file"
    SUFFIX="${SUFFIX}.mysql"
fi
if [ -n "$POSTFIX_MYSQL_PATHS" -a "$POSTFIX_MYSQL_PATHS" != 0 ]; then
    POSTFIX_MYSQL=0
    POSTFIX_MYSQL_REDHAT=0
    echo "  adding MySQL support (paths set to $POSTFIX_MYSQL_PATHS) to spec file"
    SUFFIX="${SUFFIX}.mysql_path"
fi

if [ -n "$POSTFIX_MYSQLQUERY" ]; then
    cat <<END
WARNING: POSTFIX_MYSQLQUERY has been replaced by POSTFIX_MYSQL_QUERY.
  Please unset POSTFIX_MYSQLQUERY and set POSTFIX_MYSQL_QUERY to continue.
END
    exit 1
fi
if [ "$POSTFIX_MYSQL_QUERY" = 1 ]; then
    echo "  adding support for full mysql select statements to spec file"
    SUFFIX="${SUFFIX}.mysql_query"
fi

if [ "$POSTFIX_SASL" = 1 -o "$POSTFIX_SASL" = 2 ]; then
    echo "  adding SASL v${POSTFIX_SASL} support to spec file"
    SUFFIX="${SUFFIX}.sasl${POSTFIX_SASL}"
else
    POSTFIX_SASL=
fi

[ -z "$POSTFIX_RPM_NO_WARN" -a \
	"$POSTFIX_LDAP" -gt 0 -a \
	"$POSTFIX_SASL" = 2 -a \
	$releasename = redhat -a \
	$major -le 8 ] && {
cat <<END
WARNING - WARNING - WARNING - WARNING - WARNING - WARNING - WARNING - WARNING

According to the RedHat Postfix spec file on RH versions earlier than 8.0.1 as
LDAP is compiled with SASL v1 Postfix will not work if compiled with SASL v2.

You have selected both LDAP and SASL v2 with such a RH release.

To build with this configuration set POSTFIX_RPM_NO_WARN=1 and rerun this
script.  If the resulting package works please let me know.

WARNING - WARNING - WARNING - WARNING - WARNING - WARNING - WARNING - WARNING
END
    exit 1
}

if [ "$POSTFIX_RBL_MAPS" = 1 ]; then
    cat <<END
WARNING: POSTFIX_RBL_MAPS no longer used.
  Please unset POSTFIX_RBL_MAPS to continue.
END
    exit 1
fi

if [ "$POSTFIX_IPV6" = 1 ]; then
    echo "  adding IPv6 support to spec file"
    SUFFIX="${SUFFIX}.ipv6"
fi

if [ "$POSTFIX_SPF" = 1 ]; then
    echo "  adding SPF support to spec file"
    SUFFIX="${SUFFIX}.spf"
fi

# --- REQUIRES_ZLIB --- do we require the zlib library?
REQUIRES_ZLIB=
[ "$POSTFIX_MYSQL" = 1 ]        && REQUIRES_ZLIB=1
[ "$POSTFIX_MYSQL_REDHAT" = 1 ] && REQUIRES_ZLIB=1

if [ "$POSTFIX_TLS" = 1 ]; then
    echo "  adding TLS support to spec file"
    SUFFIX="${SUFFIX}.tls"

    # Different fixes (see spec file)
    [ ${releasename} = 'redhat' -a ${major} -eq 6 ] && TLSFIX=1
    [ ${releasename} = 'redhat' -a ${major} -eq 9 ] && { TLSFIX=2; REQUIRES_ZLIB=1; }
    [ ${releasename} = 'fedora' -a ${major} -eq 1 ] && TLSFIX=2
    [ ${releasename} = 'rhel'   -a ${major} -ge 3 ] && { TLSFIX=2; REQUIRES_ZLIB=1; }
fi
if [ "$POSTFIX_VDA" = 1 ]; then
    echo "  adding VDA support to spec file"
    SUFFIX="${SUFFIX}.vda"
fi

DIST=
DEFAULT_DB=

case ${releasename} in
yellowdog)
    DEFAULT_DB=3
    ;;

rhel)
    # Stop distinguishing between enterprise | advanced server or workstation
    # as this seems rather pointless (should run on all versions I think)
    DEFAULT_DB=4
    case ${major} in
    3)
        DIST=".rhel3"
        ;;
    2)
        DEFAULT_DB=3
        DIST=".rhel21"
        ;;
    *)
        echo "ERROR: Do not recognise the version of Red Hat Enterprise Linux you are using."
        echo "ERROR: Please contact sjmudd@pobox.com with information about your distribution."
        exit 1
        ;;
    esac
    ;;

fedora)
	# distinguish fedora-core-1 / fedora-core-2
        DEFAULT_DB=4
        DIST=".fc${major}"
	;;

redhat)
    case ${major} in
    9)
	DEFAULT_DB=4
	DIST=".rh9"
	;;

    8)
	DEFAULT_DB=4
	DIST=".rh8"
	;;

    7)
	DEFAULT_DB=3

       case ${minor} in
       0) DIST=".rh70.1" ;;
       1) DIST=".rh70.1" ;;
       2) DIST=".rh72" ;;
       3) DIST=".rh73" ;;
       *) ;;
       esac
       ;;

    *)	;;
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
    # Mandrake 9
    # - assuming it uses db4
    case ${major} in
    7)	DEFAULT_DB=0
	DIST=".mdk7x"
	;;
    8)	DEFAULT_DB=3
	DIST=".mdk8x"
	;;
    9)	DEFAULT_DB=4
	DIST=".mdk9x"
	;;
    *)	DIST=".mdk"
    esac
    ;;

*)  ;;
esac

[ -z "${POSTFIX_DB}" ] && POSTFIX_DB=${DEFAULT_DB}
[ "${POSTFIX_DB}" != "${DEFAULT_DB}" -a "${POSTFIX_DB}" != 0 ] && {
    SUFFIX=".db${POSTFIX_DB}${SUFFIX}"
    echo "  adding db${POSTFIX_DB} support to spec file"
}
[ -n "${DIST}" ] && SUFFIX="${SUFFIX}${DIST}"

# set default values if they are still undefined

[ -z "$POSTFIX_CDB" ]	                   && POSTFIX_CDB=0
[ -z "$POSTFIX_DB" ]			   && POSTFIX_DB=0
[ -z "$POSTFIX_IPV6" ]			   && POSTFIX_IPV6=0
[ -z "$POSTFIX_LDAP" ]			   && POSTFIX_LDAP=0
[ -z "$POSTFIX_MYSQL" ]			   && POSTFIX_MYSQL=0
[ -z "$POSTFIX_MYSQL_PATHS" ]		   && POSTFIX_MYSQL_PATHS=0
[ -z "$POSTFIX_MYSQL_QUERY" ]		   && POSTFIX_MYSQL_QUERY=0
[ -z "$POSTFIX_MYSQL_REDHAT" ]		   && POSTFIX_MYSQL_REDHAT=0
[ -z "$POSTFIX_PCRE" ]			   && POSTFIX_PCRE=0
[ -z "$POSTFIX_PGSQL" ]			   && POSTFIX_PGSQL=0
[ -z "$POSTFIX_SASL" ]			   && POSTFIX_SASL=0
[ -z "$POSTFIX_SMTPD_MULTILINE_GREETING" ] && POSTFIX_SMTPD_MULTILINE_GREETING=0
[ -z "$POSTFIX_SPF" ]			   && POSTFIX_SPF=0
[ -z "$POSTFIX_TLS" ]			   && POSTFIX_TLS=0
[ -z "$POSTFIX_VDA" ]			   && POSTFIX_VDA=0
[ -z "$REQUIRES_ZLIB" ]			   && REQUIRES_ZLIB=0
[ -z "$TLSFIX" ]			   && TLSFIX=0

cat > ${specdir}/postfix.spec <<EOF
# W A R N I N G -- DO NOT EDIT THIS FILE -- W A R N I N G
#
# postfix.spec
#
# This file was generated automatically from ${sourcedir}/postfix.spec.in.
# If you want to build postfix with other options see make-postfix.spec in
# the same directory for instructions.
# --
EOF
sed "
s!__DISTRIBUTION__!$distribution!g
s!__MYSQL_PATHS__!$POSTFIX_MYSQL_PATHS!g
s!__REQUIRES_DB__!$POSTFIX_DB!g
s!__REQUIRES_ZLIB__!$REQUIRES_ZLIB!g
s!__SMTPD_MULTILINE_GREETING__!$POSTFIX_SMTPD_MULTILINE_GREETING!g
s!__SUFFIX__!$SUFFIX!g
s!__WITH_CDB__!$POSTFIX_CDB!g
s!__WITH_IPV6__!$POSTFIX_IPV6!g
s!__WITH_LDAP__!$POSTFIX_LDAP!g
s!__WITH_MYSQL_QUERY__!$POSTFIX_MYSQL_QUERY!g
s!__WITH_MYSQL_REDHAT__!$POSTFIX_MYSQL_REDHAT!g
s!__WITH_MYSQL__!$POSTFIX_MYSQL!g
s!__WITH_PCRE__!$POSTFIX_PCRE!g
s!__WITH_PGSQL__!$POSTFIX_PGSQL!g
s!__WITH_SASL__!$POSTFIX_SASL!g
s!__WITH_SPF__!$POSTFIX_SPF!g
s!__WITH_TLSFIX__!$TLSFIX!g
s!__WITH_TLS__!$POSTFIX_TLS!g
s!__WITH_VDA__!$POSTFIX_VDA!g
" ${sourcedir}/postfix.spec.in >> ${specdir}/postfix.spec

# end of make-postfix.spec
