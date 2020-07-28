#!/usr/bin/env bash
set -eu
fname=${1:-template.yaml}

TMP=$(mktemp /tmp/.mm.XXXXXX)
clean() { rm -f ${TMP}; }
trap clean EXIT

cat ${fname} > ${TMP}

cd $(dirname $(readlink -f ${fname}))


oifs=${IFS}
IFS="
"

for line in $(grep "## INSERT" $(basename ${fname}));do
    F2=$(<${TMP})

    scriptfile=${line//## INSERT /}
    scriptfile=${scriptfile//[ ]/}
    [[ -e ${scriptfile} ]] || { echo "Could not find ${scriptfile}"; continue ;}
    indentation="$(grep -B1 ${line} template.yaml|head -1|sed 's/^\([ ]*\).*/\1/')"
    indentation="${indentation}    "
    F1=$(sed "s/^/${indentation}/" ${scriptfile})
    cat <(echo "${F2//${line}/$F1}") > ${TMP}
done

cat ${TMP}
