#!/bin/sh
#
# # $Id: postfix-chroot.sh,v 2.2 2007/04/02 16:57:36 sjmudd Exp $
#
# postfix-chroot.sh - enable or disable Postfix chroot
#
# (C) 2003 Simon J Mudd <sjmudd@pobox.com>
#
# This script is intended to enable you to enable or disable the Postfix
# chroot environment.
#
# The functionality was previously included within my Postfix RPM package
# but the software's author stated to me that it was better to not include
# this in the default installation as it could overcomplicate Postfix's
# configuration for new users.
#
# License:
#    This program is free software; you can redistribute it and/or
#    modify it under the terms of the GNU General Public License
#    as published by the Free Software Foundation; either version 2
#    of the License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You may have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307,
#    USA.
#
#    An on-line copy of the GNU General Public License can be found
#    http://www.fsf.org/copyleft/gpl.html.

usage () {
        cat <<EOF
Usage: $myname {enable|disable}

enable  - setup Postfix chroot (removing the previous setup)
disable - remove Postfix chroot
EOF
}

# Link source file to destination directory if possible. If the link is a
# symbolic link, make a copy of the link in the destination directory,
# otherwise copy the file.

copy() {
    info 1 "  $1 -> $2"
    file=`basename $1`
    ln -f $1 $2/$file 2>/dev/null || {
        [ -L $1 2>/dev/null ] && {
            dest=`ls -l $1 | awk '{print $11}'`
            ln -sf $dest $2/$file
        } || cp -dpf $1 $2/$file
    }
}

# print an error message and exit
error () {
    echo "Error: $1" >&2
    exit 1
}

# print a warning message
warn () {
    echo "Warning: $1" >&2
}

# if $1==1 print message ($2) otherwise do nothing
info () {
    [ "$1" = 1 ] && echo "$2" || :
}

# Count the files in a particular location given by the input pattern
count_files_in () {
    echo `ls $* 2>/dev/null | wc -l`
}

##########################################################################
#
# remove chroot jail
#
# if we pass $1=quiet then do not backup master.cf or say much more than 
# we are removing the existing chroot (which is before enabling a new chroot)
#

remove_chroot () {
    verbose=1

    [ -n "$1" ] && [ "$1" = quiet ] && verbose=0

    # safety - double check before starting the chroot is valid
    [ -z "${chroot}"  ] && error "chroot (${chroot}) is not defined, exiting"
    [ "${chroot}" = / ] && error "chroot (${chroot}) is set to /, exiting"

    info 1 "removing chroot from: ${chroot}"

    # remove Postgres libraries
    pattern="${chroot}${libdir}/libpq*"
    [ $(count_files_in ${pattern}) != 0 ] && {
        info $verbose "removng Postgres files from chroot"
        rm -f ${pattern}
    }

    # remove LDAP libraries
    pattern="${chroot}${libdir}/libldap*.*so* ${chroot}${libdir}/liblber*.*so*"
    [ $(count_files_in ${pattern}) != 0 ] && {
        info $verbose "remove LDAP files from chroot"
        rm -f ${pattern}
    }

    # remove db libraries
    pattern="${chroot}/lib/libdb*.so*"
    [ $(count_files_in ${pattern}) != 0 ] && {
        info $verbose "remove db files from chroot"
        rm -f ${pattern}
    }

    # we must be in ${chroot} before calling this routine
    cd ${chroot} && {
        # remove system files
        info $verbose "remove system files from chroot"
        for i in etc/localtime usr/lib/zoneinfo/localtime \
        	usr/share/zoneinfo/localtime \
                etc/host.conf etc/resolv.conf etc/nsswitch.conf \
                etc/hosts etc/passwd etc/services \
                lib/libdb-*so* \
                lib/libnss_* lib/libresolv*; do
            [ -f ${chroot}/${i} -o -L ${chroot}/${i} ] && \
                info $verbose "  ${chroot}/${i}" && \
                rm -f ${chroot}/${i}
        done

        info $verbose "remove system directories from chroot"
        for dir in usr/share/zoneinfo usr/lib/zoneinfo usr/share usr/lib usr lib etc; do
            [ -d ${chroot}/${dir} ] && \
                info $verbose "  ${chroot}/${dir}" && \
                rmdir ${chroot}/${dir}
        done
    }

    if [ $verbose = 1 ]; then
        # remove chroot settings from master.cf
        info "backing up ${confdir}/master.cf to ${confdir}/master.cf-old.$$"
        cp ${confdir}/master.cf ${confdir}/master.cf-old.$$ && \
        awk '
BEGIN                   { IFS="[ \t]+"; OFS="\t"; }
/^#/                    { print; next; }
/^ /                    { print; next; }
$8 ~ /(proxymap|local|pipe|virtual)/    { print; next; }
$5 == "y"               { $5="n"; print $0; next; }
                        { print; }
' ${confdir}/master.cf-old.$$ > ${confdir}/master.cf
    fi
}

#
##########################################################################

##########################################################################
#
# setup chroot jail

setup_chroot() {
    verbose=1

    # Check master.cf is where we expect it
    [ -f ${confdir}/master.cf ] || error "${confdir}/master.cf missing, exiting"
    info $verbose "setting up chroot at: ${chroot}"

    # setup the chroot directory structure
    info $verbose "setup chroot directory structure"
    for i in /etc /lib /usr/lib/zoneinfo /usr/share/zoneinfo; do
        info $verbose "  ${chroot}${i}"
        mkdir -p ${chroot}${i}
    done

    # copy system files into chroot environment
    info $verbose "copy system files into chroot"
    for i in /etc/localtime /usr/lib/zoneinfo/localtime \
	    /usr/share/zoneinfo/localtime \
            /etc/host.conf /etc/resolv.conf /etc/nsswitch.conf \
            /etc/hosts /etc/services; do
        [ -e ${i} ] && copy ${i} `/usr/bin/dirname ${chroot}${i}`
    done

    # copy /etc/passwd file if needed
    [ `postconf -h local_recipient_maps | grep -q proxy:unix:passwd.byname; echo $?` = 0 ] || { \
        info $verbose "copy (cleaned) /etc/passwd into chroot"
        awk -F: '{ print $1 ":*:" $3 ":" $4 "::/no/home:/bin/false" }' /etc/passwd > ${chroot}/etc/passwd
    } || :

    # check smtpd's dependencies to determine which libraries need to
    # copied into the chroot

    smtpd=${daemondir}/smtpd
    dependencies=`/usr/bin/ldd ${smtpd} | awk '{print $1}'`

    # determine if the postgresql library is needed
    echo ${dependencies} | grep -q libpq && {
        info $verbose "copy Postgresql libraries into chroot"
        copy ${libdir}/libpq.so.2 ${chroot}${libdir}/
        ldconfig -n ${chroot}${libdir}		# not convinced this is necessary
    }

    # determine if the LDAP libraries are needed
    echo ${dependencies} | grep -q libldap && {
        info $verbose "copy LDAP libraries into chroot"
        for i in ${libdir}/libldap*.*so* \
                 ${libdir}/libldap_r.*so* \
                 ${libdir}/liblber*.*so*; do
              copy $i ${chroot}${libdir}/
        done
        ldconfig -n ${chroot}${libdir}		# not convinced this is necessary
    }

    # determine which db is needed
    dbdeps=`/usr/bin/ldd ${smtpd} | awk '{print $1}' | grep libdb`
    [ -n "${dbdeps}" ] && {
        info $verbose "copy db library (${dbdeps}) into chroot"
        copy /lib/${dbdeps} ${chroot}/lib/
        ldconfig -n ${chroot}/lib		# not convinced this is necessary
    }

    # copy system files into chroot environment
    info $verbose "copy system files into chroot"

    # determine glibc version
    LIBCVER=`ls -l /lib/libc.so.6* | sed "s/.*libc-\(.*\).so$/\1/g"`
    # copy the relevant parts of glibc into the chroot
    for i in compat dns files hesoid ldap nis nisplus winbind wins; do
      [ -e /lib/libnss_${i}-${LIBCVER}.so ] && copy /lib/libnss_${i}-${LIBCVER}.so ${chroot}/lib/
      [ -e /lib/libnss_${i}.so ]            && copy /lib/libnss_${i}.so            ${chroot}/lib/
      [ -e /lib/libnss_${i}.so.2 ]          && copy /lib/libnss_${i}.so.2          ${chroot}/lib/
    done
    [ -e /lib/libnss_db.so.2.0.0 ] && copy /lib/libnss_db.so.2.0.0 ${chroot}/lib/
    [ -e /lib/libresolv-${LIBCVER}.so ]   && copy /lib/libresolv-${LIBCVER}.so   ${chroot}/lib/
    [ -e /lib/libresolv-${LIBCVER}.so.2 ] && copy /lib/libresolv-${LIBCVER}.so.2 ${chroot}/lib/
    ldconfig -n ${chroot}/lib		# not convinced this is necessary

    # chroot master.cf change all lines except pipe, local, proxymap and
    # virtual
    info $verbose "backing up ${confdir}/master.cf to ${confdir}/master.cf-old.$$"
    cp ${confdir}/master.cf ${confdir}/master.cf-old.$$ && \
    awk '
BEGIN                   { IFS="[ \t]+"; OFS="\t"; }
/^#/                    { print; next; }
/^ /                    { print; next; }
$8 ~ /(proxymap|local|pipe|virtual)/    { print; next; }
$5 == "n"               { $5="y"; print $0; next; }
                        { print; }
' ${confdir}/master.cf-old.$$ > ${confdir}/master.cf
}

# end setup chroot jail
#
##########################################################################

##########################################################################
#
# stop Postfix (if running)

stop_postfix () {
    ${daemondir}/master -t 2>/dev/null && return
    info 1 "Stopping Postfix, please restart it after checking the changes"
    ( cd ${chroot} && kill `sed 1q pid/master.pid` )
    sleep 3
}

#
##########################################################################

myname=`basename $0`
[ $# = 1 ] || { usage; exit 1; }

# set the umask to the RH default in case this has been modified
umask 0022
confdir=/etc/postfix
libdir=/usr/lib
postconf=/usr/sbin/postconf
[ `id -u` = 0    ] || error "your must be root to run this script"
[ -d ${confdir}  ] || error "no postfix directory ${confdir}"
[ -x ${postconf} ] || error "can not find postconf"
chroot=`${postconf} -c ${confdir} -h queue_directory`
[ -d ${chroot}   ] || error "no postfix queue_directory ${chroot}"
daemondir=`${postconf} -c ${confdir} -h daemon_directory`

# See how we were called.
case "$1" in
  enable)
        stop_postfix
# quiet doesn't backup master.cf or say much at all
        remove_chroot quiet
        setup_chroot
        ;;
  disable)
        stop_postfix
        remove_chroot
        ;;
  *)
	usage
        exit 1
esac

exit $?
