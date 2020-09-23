#!/bin/bash
debug="rm"

${debug} -fv ~/Library/Preferences/*jetbrains*plist
${debug} -vf ~/Library/Application\ Support/JetBrains/*/eval/*key


echo "Search all machine-id and evl\* references"
open ~/Library/Preferences/com.apple.java.util.prefs.plist
read

${debug} -vf ~/Library/Application\ Support/JetBrains/GoLand*/options/other.xml
ps ax | grep cfprefsd
