#!/bin/sh
#
# # $Id: postfix-chroot.sh,v 1.1.2.2 2003/07/23 21:26:25 sjmudd Exp $
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
# otherwise copy the file.  Log to /var/log/maillog what we are doing.

copy() {
    info "  $1 -> $2"
    file=`basename $1`
    ln -f $1 $2/$file 2>/dev/null || {
        [ -L $1 2>/dev/null ] && {
            dest=`ls -l $1 | awk '{print $11}'`
            ln -sf $dest $2/$file
        } || cp -dpf $1 $2/$file
    }
}

error () {
    echo "Error: $1" >&2
    exit 1
}

warn () {
    echo "Warning: $1" >&2
}

info () {
    echo "$1"
}

##########################################################################
#
# remove chroot jail
#

remove_chroot () {
    # safety - double check before starting the chroot is valid
    [ -z "${chroot}"  ] && error "chroot (${chroot}) is not defined, exiting"
    [ "${chroot}" = / ] && error "chroot (${chroot}) is set to /, exiting"

    info "removing chroot from: ${chroot}"

    # remove Postgres libraries
    info "removng Postgres files from chroot (if any)"
    rm -f ${chroot}${libdir}/libpq*

    # remove LDAP libraries
    info "remove LDAP files from chroot (if any)"
    rm -f ${chroot}${libdir}/libldap*.so*
    rm -f ${chroot}${libdir}/liblber.so*

    # remove db libraries
    info "remove db files from chroot (if any)"
    rm -f ${chroot}/lib/libdb*.so*

    # we must be in ${chroot} before calling this routine
    cd ${chroot} && {
        # remove system files
        info "remove system files from chroot:"
        for i in etc/localtime usr/lib/zoneinfo/localtime \
                etc/host.conf etc/resolv.conf etc/nsswitch.conf \
                etc/hosts etc/passwd etc/services \
                lib/libdb-*so* \
                lib/libnss_* lib/libresolv*; do
            [ -f ${chroot}/${i} -o -L ${chroot}/${i} ] && \
                info "  ${chroot}/${i}" && \
                rm -f ${chroot}/${i}
        done

        info "remove system directories from chroot:"
        for dir in usr/lib/zoneinfo usr/lib usr lib etc; do
            [ -d ${chroot}/${dir} ] && \
                info "  ${chroot}/${dir}" && \
                rmdir ${chroot}/${dir}
        done
    }

    # remove chroot settings from master.cf
    info "backing up ${confdir}/master.cf to ${confdir}/master.cf-old"
    cp ${confdir}/master.cf ${confdir}/master.cf-old && \
    awk '
BEGIN                   { IFS="[ \t]+"; OFS="\t"; }
/^#/                    { print; next; }
/^ /                    { print; next; }
$8 ~ /(proxymap|local|pipe|virtual)/    { print; next; }
$5 == "y"               { $5="n"; print $0; next; }
                        { print; }
' < ${confdir}/master.cf-old > ${confdir}/master.cf

}

#
##########################################################################

##########################################################################
#
# setup chroot jail

setup_chroot() {
    # Check master.cf is where we expect it
    [ -f ${confdir}/master.cf ] || error "${confdir}/master.cf missing, exiting"
    info "setting up chroot at: ${chroot}"

    # setup the chroot directory structure
    info "setup chroot directory structure"
    for i in /etc /lib /usr/lib/zoneinfo; do
        info "  ${chroot}${i}"
        mkdir -p ${chroot}${i}
    done

    # copy system files into chroot environment
    info "copy system files into chroot"
    for i in /etc/localtime /usr/lib/zoneinfo/localtime \
            /etc/host.conf /etc/resolv.conf /etc/nsswitch.conf \
            /etc/hosts /etc/services; do
        [ -e ${i} ] && copy ${i} `/usr/bin/dirname ${chroot}${i}`
    done

    # copy /etc/passwd file if needed
###    [ `postconf -h local_recipient_maps | grep -q proxy:unix:passwd.byname; echo $?` = 0 ] || { \
###

        info "copy (cleaned) /etc/passwd into chroot"
        awk -F: '{ print $1 ":*:" $3 ":" $4 "::/no/home:/bin/false" }' /etc/passwd > ${chroot}/etc/passwd


###    } || :

    # check smtpd's dependencies to determine which libraries need to
    # copied into the chroot

    smtpd=${daemondir}/smtpd
    dependencies=`/usr/bin/ldd ${smtpd} | awk '{print $1}'`

    # determine if the postgresql library is needed
    echo ${dependencies} | grep -q libpq && {
        info "copy Postgresql libraries into chroot"
        copy ${libdir}/libpq.so.2 ${chroot}${libdir}/
        ldconfig -n ${chroot}${libdir}		# not convinced this is necessary
    }

    # determine if the LDAP libraries are needed
    echo ${dependencies} | grep -q libldap && {
        info "copy LDAP libraries into chroot"
        for i in ${libdir}/libldap*.so* \
                 ${libdir}/libldap_r.so* \
                 ${libdir}/liblber.so*; do
              copy $i ${chroot}${libdir}/
        done
        ldconfig -n ${chroot}${libdir}		# not convinced this is necessary
    }

    # determine which db is needed
    dbdeps=`/usr/bin/ldd ${smtpd} | awk '{print $1}' | grep libdb`
    [ -n "${dbdeps}" ] && {
        info "copy db library (${dbdeps}) into chroot"
        copy /lib/${dbdeps} ${chroot}/lib/
        ldconfig -n ${chroot}/lib		# not convinced this is necessary
    }

    # copy system files into chroot environment
    info "copy system files into chroot"

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
    info "backing up ${confdir}/master.cf to ${confdir}/master.cf-old"
    cp ${confdir}/master.cf ${confdir}/master.cf-old && \
    awk '
BEGIN                   { IFS="[ \t]+"; OFS="\t"; }
/^#/                    { print; next; }
/^ /                    { print; next; }
$8 ~ /(proxymap|local|pipe|virtual)/    { print; next; }
$5 == "n"               { $5="y"; print $0; next; }
                        { print; }
' < ${confdir}/master.cf-old > ${confdir}/master.cf

}

# end setup chroot jail
#
##########################################################################

##########################################################################
#
# stop Postfix (if running)

stop_postfix () {
    ${daemondir}/master -t 2>/dev/null && return
    info "Stopping Postfix, please restart it after checking the changes"
}

#
##########################################################################

myname=`basename $0`
[ $# = 1 ] || { usage; exit 1; }

confdir=/etc/postfix
libdir=/usr/lib
postconf=/usr/sbin/postconf
[ `id -u` = 0    ] || error "your must be root to run this script"
[ -d ${confdir}  ] || error "no postfix directory ${confdir}"
[ -x ${postconf} ] || error "can not find postconf"
chroot=`${postconf} -c ${confdir} -h queue_directory`
daemondir=`${postconf} -c ${confdir} -h daemon_directory`

# See how we were called.
case "$1" in
  enable)
        stop_postfix
        remove_chroot
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
