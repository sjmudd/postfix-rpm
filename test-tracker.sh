#!/bin/sh
#
# script to run vcheck and get a nice output of files that may need updating
# - borrowed from OpenPKG and adapted for my RPM

# update postfix.spec.vc with the values from postfix.spec.in

vcfile=postfix.spec.vc
specfile=postfix.spec.in

for variable in $(grep "^prog V_[a-z0-9]* = " $vcfile | awk '{ print $2 }')
do
    echo "variable: ${variable}"
    value=$(grep "^%define ${variable}[ 	]" $specfile | awk '{ print $3 }')
    echo "- value:   ${value}"

    # now check the value in $vcfile
    if [ -n "${value}" ]; then
        vcvalue=$(grep -1 "^prog ${variable}" $vcfile | grep "version   =" | awk '{ print $3 }')
        echo "- vcvalue: ${vcvalue}"

        # update vcfile if value is different
        if [ "${vcvalue}" != "${value}" ]; then
            echo "Updating $vcfile with ${variable} version ${value}"
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
        echo "warning - no value for ${variable}"
    fi
    echo ""
done

LANG= LC_CTYPE= perl tracker.pl $specfile
