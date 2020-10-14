#!/usr/bin/env bash
# https://blog.chmouel.com/2020/07/28/tekton-yaml-templates-and-script-feature/
set -eu
fname=${1:-template.yaml}

TMP=$(mktemp /tmp/.mm.XXXXXX)
clean() { rm -f "${TMP}"; }
trap clean EXIT

cat "${fname}" > "${TMP}"

cd "$(dirname "$(readlink -f "${fname}")")"

IFS="
"
grep "## INSERT" "$(basename "${fname}")"|while read -r line;do
    F2=$(<"${TMP}")

    scriptfile=${line//## INSERT /}
    scriptfile=${scriptfile//[ ]/}
    [[ -e ${scriptfile} ]] || { echo "Could not find ${scriptfile}"; continue ;}
    indentation="$(grep -B1 "${line}" template.yaml|head -1|sed 's/^\([ ]*\).*/\1/')"
    indentation="${indentation}  "
    F1=$(sed -e "s/^/${indentation}/" "${scriptfile}"|sed 's/^\s*$//')
    cat <(echo "${F2//${line}/$F1}") > "${TMP}"
done

cat "${TMP}"
