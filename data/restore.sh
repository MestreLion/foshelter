#!/usr/bin/env bash
#
# Copy Fallout Shelter save files to Android device using ADB
#
# Copyright (C) 2018 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

savedir=/mnt/sdcard/Android/data/com.bethsoft.falloutshelter/files

if !(($#)); then
	echo "Copy Fallout Shelter save files to Android device using ADB" >&2
	echo "Usage: restore.sh FILES" >&2
	exit 1
fi

adb push --sync "$@" "$savedir"
