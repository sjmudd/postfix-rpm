#!/bin/sh
#
# $Id: make-postfix.spec,v 2.12 2003/07/13 21:10:38 sjmudd Exp $
#
# Script to create the postfix.spec file from postfix.spec.in
#
# It's behaviour depends on the version of Red Hat Linux it is running
# on, but this could be extended to other non-redhat distributions.
# 
# The following external variables if set to 1 affect the behaviour
#
# POSTFIX_MYSQL		include support for MySQL's MySQL packages
# POSTFIX_MYSQL_REDHAT	include support for RedHat's mysql packages
# POSTFIX_MYSQL_PATHS	include support for locally installed mysql binary,
#			providing the colon seperated include and
#			library paths ( /usr/include/mysql:/usr/lib/mysql )
# POSTFIX_MYSQL_QUERY	include support for writing full select statements
#			in mysql maps
# POSTFIX_MYSQL_DICT_REG
#			include support for mysql: dict_register patch
# POSTFIX_LDAP		include support for openldap packages
# POSTFIX_PCRE		include support for pcre maps
# POSTFIX_PGSQL		include support for PostGres database
# POSTFIX_PGSQL2	additional experimental patches provided by
#			George Barbarosie <georgeb@intelinet.ro>
# POSTFIX_SASL		include support for SASL (1, 2 or 0 to disable)
# POSTFIX_TLS		include support for TLS
# POSTFIX_IPV6		include support for IPv6 (don't use with TLS)
# POSTFIX_VDA		include support for Virtual Delivery Agent
# POSTFIX_SMTPD_MULTILINE_GREETING
#			include support for multitline SMTP banner
#
# These two values will be setup according to your distribution, but
# you may override them.
# POSTFIX_DB		add support for dbX, (3, 4, or 0 to disable)
# POSTFIX_INCLUDE_DB	include the dbX directory when compiling (0,1)
#			and linking, basically a hack to allow db3 to
#			work on rh6x. Maybe I should generalise this
#			later.
#
# POSTFIX_DISABLE_CHROOT	disable creation of chroot environment
# POSTFIX_CDB		support for Constant Database, CDB, by Michael Tokarev
#			<mjt@corpit.ru>, as originally devised by djb.
#
# Distribution Specific Configurations
# ------------------------------------
#
# Please advise me if any of these assumptions are incorrect.
#
# Red Hat Linux Enterprise and Advanced Server 2.1 require
# REQUIRES_INIT_D	add /etc/init.d/ to requires list
# POSTFIX_DB=3		add db3 package to requires list
# LDAP support is included
#
# Red Hat Linux 9 requires
# REQUIRES_INIT_D	add /etc/init.d/ to requires list
# POSTFIX_DB=4		add db4 package to requires list
#
# Red Hat Linux 8 requires
# REQUIRES_INIT_D	add /etc/init.d/ to requires list
# POSTFIX_DB=4		add db4 package to requires list
#
# Red Hat Linux 7.x requires
# REQUIRES_INIT_D	add /etc/init.d/ to requires list
# POSTFIX_DB=3		add db3 package to requires list
#
# Red Hat Linux MAY require (according to configuration)
# TLSFIX=1		enable a fix for TLS support on RH 6.2 (see spec file)
# TLSFIX=2		enable a fix for TLS support on RH 9 (see spec file)
# POSTFIX_DB=3		add db3 package to requires list
# POSTFIX_INCLUDE_DB=1	add /usr/include/db3 to the includes list
#			and the db-3.1 library to the build instructions
#
# To rebuild the spec file, set the appropriate environment
# variables and do the following:
#
# cd `rpm --eval '%{_sourcedir}'`
# export POSTFIX_MYSQL=1	# for example
# sh make-postfix.spec
# cd `rpm --eval '%{_specdir}'`
# rpm -ba postfix.spec

# ensure that these variables are NOT set from outside
SUFFIX=			# RPM package suffix
REQUIRES_INIT_D=	# do we require /etc/init.d? (rh 7 and later)
TLSFIX=			# Apply "fixes" to TLS patches

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

if [ "$POSTFIX_MYSQL_DICT_REG" = 1 ]; then
    echo "including patch for dict_register fix for proxy:mysql:mysql-xxx.cf"
fi

if [ "$POSTFIX_CDB" = 1 ]; then
    echo "  adding CDB support to spec file"
    SUFFIX="${SUFFIX}.cdb"
fi

# LDAP support is provided by default on:
#	redhat >= 7.2
#	rhes, rhas >= 2.1
#	yellowdog >= 2.3.
# Therefore if adding LDAP support on these platforms don't include the .ldap
# suffix:  It is assumed.  We also automatically include LDAP support on
# these platforms, unless it has been explicitly disabled.

DEFAULT_LDAP=0
case ${releasename} in
mandrake)
    # Not sure from when Mandrake supported LDAP,
    # however it's now the default.
    DEFAULT_LDAP=1
    ;;

rhes|rhas)
    DEFAULT_LDAP=1
    ;;

redhat)
    [ "${major}" -eq 7 -a "${minor}" -ge 2 ] && DEFAULT_LDAP=1
    [ "${major}" -ge 8 ] && DEFAULT_LDAP=1
    ;;

yellowdog)
    [ "${major}" -eq 2 -a "${minor}" -ge 3 ] && DEFAULT_LDAP=1
    [ "${major}" -ge 3 ] && DEFAULT_LDAP=1
    ;;
esac
test -z "${POSTFIX_LDAP}" && POSTFIX_LDAP=${DEFAULT_LDAP}
if [ "${POSTFIX_LDAP}" = 1 ]; then
    echo "  adding LDAP support to spec file"
    [ "${POSTFIX_LDAP}" != "${DEFAULT_LDAP}" ] && SUFFIX="${SUFFIX}.ldap"
fi

if [ "$POSTFIX_PCRE" = 1 ]; then
    echo "  adding PCRE support to spec file"
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
if [ -n "$POSTFIX_MYSQL_PATHS" ]; then
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
POSTFIX_SASL_LIBRARY=notused
if [ "$POSTFIX_SASL" = 1 -o "$POSTFIX_SASL" = 2 ]; then
    echo "  adding SASL v${POSTFIX_SASL} support to spec file"
    SUFFIX="${SUFFIX}.sasl${POSTFIX_SASL}"

    # which is the "-devel" library used for SASL?
    case ${distribution} in
    mandrake-*)
        POSTFIX_SASL_LIBRARY=libsasl-devel
	;;
    *)
	POSTFIX_SASL_LIBRARY=cyrus-sasl-devel
	;;
    esac
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

if [ "$POSTFIX_TLS" = 1 ]; then
    if [ "$POSTFIX_IPV6" = 1 ]; then
        cat <<END
ERROR: POSTFIX_IPV6 already includes the TLS patches.
  Please unset POSTFIX_TLS to continue
END
        exit 1
    fi

    echo "  adding TLS support to spec file"
    SUFFIX="${SUFFIX}.tls"

    # Different fixes (see spec file)
    [ ${releasename} = 'redhat' -a ${major} = 6 ] && TLSFIX=1
    [ ${releasename} = 'redhat' -a ${major} = 9 ] && TLSFIX=2
fi
if [ "$POSTFIX_VDA" = 1 ]; then
    echo "  adding VDA support to spec file"
    SUFFIX="${SUFFIX}.vda"
fi
if [ "$POSTFIX_DISABLE_CHROOT" = 1 ]; then
    echo "  disabling chroot environment in spec file"
    SUFFIX="${SUFFIX}.nochroot"
fi

DIST=
DEFAULT_DB=

case ${releasename} in
yellowdog)
    DEFAULT_DB=3
    REQUIRES_INIT_D=1
    ;;

rhes|rhas)
    DEFAULT_DB=3
    REQUIRES_INIT_D=1
    [ ${releasename} = "rhes" ] && DIST=".rhes21"
    [ ${releasename} = "rhas" ] && DIST=".rhas21"
    ;;

redhat)
    case ${major} in
    9)
	DEFAULT_DB=4
	REQUIRES_INIT_D=1
	DIST=".rh9"
	;;

    8)
	DEFAULT_DB=4
	REQUIRES_INIT_D=1
	DIST=".rh8"
	;;

    7)
	DEFAULT_DB=3
	REQUIRES_INIT_D=1

       case ${minor} in
       0) DIST=".rh70.1" ;;
       1) DIST=".rh70.1" ;;
       2) DIST=".rh72" ;;
       3) DIST=".rh73" ;;
       *) ;;
       esac
       ;;

    6)
	# This may need checking
	DEFAULT_DB=0
	[ -z "$POSTFIX_DB" ] && POSTFIX_DB=${DEFAULT_DB}
	[ "${POSTFIX_DB}" != "${DEFAULT_DB}" ] && POSTFIX_INCLUDE_DB=1
	DIST=".rh6x"
	;;

    5)
	# Tested on an updated rh5.2
	DEFAULT_DB=0
	[ -z "$POSTFIX_DB" ] && POSTFIX_DB=${DEFAULT_DB}
	DIST=".rh5x"
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
	MANPAGE_SUFFIX=".bz2"
	DIST=".mdk8x"
	;;
    9)	DEFAULT_DB=4
	MANPAGE_SUFFIX=".bz2"
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

[ -z "$REQUIRES_INIT_D" ]		   && REQUIRES_INIT_D=0
[ -z "$POSTFIX_INCLUDE_DB" ]		   && POSTFIX_INCLUDE_DB=0
[ -z "$POSTFIX_DB" ]			   && POSTFIX_DB=0
[ -z "$POSTFIX_LDAP" ]			   && POSTFIX_LDAP=0
[ -z "$POSTFIX_MYSQL" ]			   && POSTFIX_MYSQL=0
[ -z "$POSTFIX_MYSQL_REDHAT" ]		   && POSTFIX_MYSQL_REDHAT=0
[ -z "$POSTFIX_MYSQL_PATHS" ]		   && POSTFIX_MYSQL_PATHS=0
[ -z "$POSTFIX_MYSQL_QUERY" ]		   && POSTFIX_MYSQL_QUERY=0
[ -z "$POSTFIX_MYSQL_DICT_REG" ]	   && POSTFIX_MYSQL_DICT_REG=0
[ -z "$POSTFIX_PCRE" ]			   && POSTFIX_PCRE=0
[ -z "$POSTFIX_PGSQL" ]			   && POSTFIX_PGSQL=0
[ -z "$POSTFIX_PGSQL2" ]		   && POSTFIX_PGSQL2=0
[ -z "$POSTFIX_SASL" ]			   && POSTFIX_SASL=0
[ -z "$POSTFIX_TLS" ]			   && POSTFIX_TLS=0
[ -z "$POSTFIX_VDA" ]			   && POSTFIX_VDA=0
[ -z "$TLSFIX" ]			   && TLSFIX=0
[ -z "$POSTFIX_SMTPD_MULTILINE_GREETING" ] && POSTFIX_SMTPD_MULTILINE_GREETING=0
[ -z "$POSTFIX_DISABLE_CHROOT" ]	   && POSTFIX_DISABLE_CHROOT=0
[ -z "$POSTFIX_CDB" ]	                   && POSTFIX_CDB=0
[ -z "$POSTFIX_IPV6" ]			   && POSTFIX_IPV6=0

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
s!__INCLUDE_DB__!$POSTFIX_INCLUDE_DB!g
s!__REQUIRES_DB__!$POSTFIX_DB!g
s!__REQUIRES_INIT_D__!$REQUIRES_INIT_D!g
s!__DISTRIBUTION__!$distribution!g
s!__SMTPD_MULTILINE_GREETING__!$POSTFIX_SMTPD_MULTILINE_GREETING!g
s!__SUFFIX__!$SUFFIX!g
s!__LDAP__!$POSTFIX_LDAP!g
s!__MYSQL__!$POSTFIX_MYSQL!g
s!__MYSQL_REDHAT__!$POSTFIX_MYSQL_REDHAT!g
s!__MYSQL_PATHS__!$POSTFIX_MYSQL_PATHS!g
s!__MYSQL_QUERY__!$POSTFIX_MYSQL_QUERY!g
s!__MYSQL_DICT_REG__!$POSTFIX_MYSQL_DICT_REG!g
s!__PCRE__!$POSTFIX_PCRE!g
s!__PGSQL__!$POSTFIX_PGSQL!g
s!__PGSQL2__!$POSTFIX_PGSQL2!g
s!__SASL__!$POSTFIX_SASL!g
s!__SASL_LIBRARY__!$POSTFIX_SASL_LIBRARY!g
s!__TLS__!$POSTFIX_TLS!g
s!__TLSFIX__!$TLSFIX!g
s!__VDA__!$POSTFIX_VDA!g
s!__DISABLE_CHROOT__!$POSTFIX_DISABLE_CHROOT!g
s!__CDB__!$POSTFIX_CDB!g
s!__MANPAGE_SUFFIX__!$MANPAGE_SUFFIX!g
s!__IPV6__!$POSTFIX_IPV6!g
" `rpm --eval '%{_sourcedir}'`/postfix.spec.in >> `rpm --eval '%{_specdir}'`/postfix.spec

# end of make-postfix.spec
