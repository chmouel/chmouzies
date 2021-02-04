#!/usr/bin/env bash
# resizes the window to full height and 50% width and moves into the center of the secreen
# adapted from https://unix.stackexchange.com/a/53228 so we center the window by
# default unless we have the rotate argument and then we rotate the window
# around the screen from 1/3 => 2/3 => 3/3

#define the height in px of the top system-bar:
TOPMARGIN=27

#sum in px of all horizontal borders:
RIGHTMARGIN=10

# get width of screen and height of screen
SCREEN_WIDTH=$(xwininfo -root | awk '$1=="Width:" {print $2}')
SCREEN_HEIGHT=$(xwininfo -root | awk '$1=="Height:" {print $2}')

PREVIOUS=$HOME/.cache/rotatewindow/cache
[[ -d $(dirname ${PREVIOUS}) ]] || mkdir -p $(dirname ${PREVIOUS})

[[ ${1} == "rotate" ]] && rotatearound=true

eval $(xwininfo -id $(xdotool getactivewindow) |
    sed -n -e "s/^ \+Absolute upper-left X: \+\([0-9]\+\).*/currentx=\1/p" \
           -e "s/^ \+Absolute upper-left Y: \+\([0-9]\+\).*/currenty=\1/p" \
           -e "s/^ \+Width: \+\([0-9]\+\).*/currentw=\1/p" \
           -e "s/^ \+Height: \+\([0-9]\+\).*/currenth=\1/p" )

# new width and height
W=$(( $SCREEN_WIDTH / 2 - $RIGHTMARGIN ))
H=$(( $SCREEN_HEIGHT - 2 * $TOPMARGIN ))

# moving to the center
X=$(( $SCREEN_WIDTH / 3 ))

if [[ ${currentx} > ${X} ]];then
    echo "droite" > ${PREVIOUS}
elif [[ ${X} > ${currentx} ]];then
    echo "gauche" > ${PREVIOUS}
elif [[ -n ${rotatearound} && -e /tmp/previous ]]; then
    previous=$(cat ${PREVIOUS})
    if [[ ${previous} == "gauche" ]];then
        # Go a droite
        # xte 'keydown Super_L' 'keydown Shift_L' 'keydown Right' 'keyup Right' 'keyup Shift_L' 'keyup Super_L'
        # exit 0
        X=${SCREEN_WIDTH}
    elif [[ ${previous} == "droite" ]];then
        # Go a gauche
        # xte 'keydown Super_L' 'keydown Shift_L' 'keydown Left' 'keyup Left' 'keyup Shift_L' 'keyup Super_L'
        # exit 0
        X=0
    fi
fi

Y=$TOPMARGIN

wmctrl -r :ACTIVE: -b remove,maximized_vert,maximized_horz && wmctrl -r :ACTIVE: -e 0,$X,$Y,$W,$H
