#!/bin/sh
#
# $Header: /home/sjmudd/tmp/cvsroot/postfix-rpm/postfix-tracker.sh,v 1.1.4.1 2005/02/07 18:41:24 sjmudd Exp $
#
# Postfix version tracker (C) 2004 Simon J Mudd
#
# script to run vcheck and get a nice output of files that may need
# updating
# - borrowed from OpenPKG and adapted for my RPM
#
# update postfix.spec.vc with the values from postfix.spec.in

[ -n "$DEBUG" ] && set -x

verbose=
vcfile=postfix.spec.vc
specfile=postfix.spec.in

for variable in $(grep "^prog V_[a-z0-9]* = " $vcfile | awk '{ print $2 }')
do
    [ -n "$verbose" ] && echo "variable: ${variable}"
    value=$(grep "^%define ${variable}[ 	]" $specfile | awk '{ print $3 }')
    [ -n "$verbose" ] && echo "- value:   ${value}"

    # now check the value in $vcfile
    if [ -n "${value}" ]; then
        vcvalue=$(grep -1 "^prog ${variable}" $vcfile | grep "version   =" | awk '{ print $3 }')
        [ -n "$verbose" ] && echo "- vcvalue: ${vcvalue}"

        # update vcfile if value is different
        if [ "${vcvalue}" != "${value}" ]; then
            [ -n "$verbose" ] && echo "Updating $vcfile with ${variable} version ${value}"
            # careful with the spaces
            ed <<EOF $vcfile
# uncomment this to use for debugging
#H
# uncomment this to show what is being matched
#/^prog ${variable} /,/version   = ${vcvalue}/ n
/^prog ${variable} /,/version   = ${vcvalue}/ s/version   =.*\$/version   = ${value}/
w
q
EOF
        fi
    else
        [ -n "$verbose" ] && echo "warning - no value for ${variable}"
    fi
    [ -n "$verbose" ] && echo ""
done

LANG= LC_CTYPE= perl tracker.pl --address=sjmudd+postfix-tracker@wl0.org $specfile
