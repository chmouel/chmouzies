#!/usr/bin/env bash
# need hub - https://github.com/github/hub
# need colout - https://nojhan.github.com/colout/
# need terminal-notifier - https://github.com/julienXX/terminal-notifier
# If you don't want those just remove the colout filtering (no colours)
# and replace terminal-notifer by something else, (i.e: notify-send on linux)
# not that specific to ci.centos you can probably adapt it to whatever,
# I use centos.png for terminal-notifier argument, feel free to have something
# else or or redefine to your path.
SED=sed
type -p gsed >/dev/null 2>/dev/null && SED=gsed

[[ $1 == "-n" ]] && { nofollow=yes; shift ;}
wait=5 # in seconds

tempf=$(mktemp) || exit
trap "rm -f -- $tempf" EXIT

function blackgreen() { msg="$@";echo "\e[40;38;5;82m${msg}\e[0m" ;}
function blackred() { msg="$@";echo "\e[40;91;5;82m${msg}\e[0m" ;}

if [[ ${1} == https://*pull* ]];then
    PR=${1}
    API_PR=$(echo ${1}|sed -e 's/github.com/api.github.com\/repos/' -e 's,pull/,pulls/,' -e 's,$,/commits,')
    COMMIT_URL=$(curl -s -H "Authorization: token $(git config --get github.oauth-token)" ${API_PR}|jq -r '.[-1].url')/status
    [[ -z ${COMMIT_URL} ]] && { echo "I can't find SHA "; exit 1 ;}
    RESULT=$(curl -s -H "Authorization: token $(git config --get github.oauth-token)" ${COMMIT_URL} | \
                 jq -r '.statuses[] | select (.target_url|test("ci.centos.org")).target_url')
    [[ -n ${RESULT} ]] && RESULT=${RESULT}consoleText
elif [[ ${1} == https://ci.centos.org* ]];then
    url=$1
    [[ $url == *[0-9]/ || $url == *[0-9] ]] && url=${url}/consoleText
    [[ $url == *console ]] && url=${url}Text
    RESULT=${url}
else
    RESULT=$(hub ci-status -v ${1}|${SED} -E -n '/^.*ci.centos.org PR build  .*https/ { s/.*(https:...*)/\1consoleText/;p;}')
fi

[[ -z ${RESULT} ]] && { echo "No job detected"; exit 1;}

while true;do
    curl -s ${RESULT} > ${tempf}

    cmd=cat
    [[ -n ${refreshed} ]] && cmd=tail

    ${cmd} ${tempf} | sed -e 's/^M/\n/'|colout "^(\+(\+)?) (.*)" rainbow | \
        colout '(Finished): (\w+)' blue,yellow|colout 'to (\w+) with url (https://ci.centos.org.*) and message: ' yellow

    [[ -n ${nofollow} ]] && break

    if egrep -q "^Finished: " ${tempf};then
        [[ -z ${refreshed} ]] && break # no need to notify when we haven't done a tailing
        STATUS=$(grep "^Finished: "  ${tempf}|sed 's/Finished: //')
        terminal-notifier -title "Build ${STATUS}" \
                          -message $(echo ${RESULT}|sed -e 's/.*job\///;s,/$,,;s,/consoleText,,') -appIcon \
                          $HOME/GIT/gist/hub-cico-last/centos.png -open ${RESULT/consoleText/console} -ignoreDnD

        [[ ${STATUS} == "SUCCESS" ]] && EXITCODE=0  || EXITCODE=1
        break
    fi

    echo
    sleep ${wait}
    echo -e $(blackred "...")
    echo
    refreshed=true
done

[[ -n ${EXITCODE} ]] && exit ${EXITCODE}
