#!/usr/bin/env bash
#
# Backup Fallout Shelter save files from Android device using ADB
#
# Copyright (C) 2018 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

savedir=/mnt/sdcard/Android/data/com.bethsoft.falloutshelter/files

dir=${1:-.}

if (($# > 1)) || ! [[ -d "$dir" ]]; then
	echo "Backup Fallout Shelter save files from Android device" >&2
	echo "Usage: ./backup.sh [DIR]" >&2
	exit 1
fi

adb pull -a "$savedir"/Vault{1,2,3}.sav{,.bkp} "$dir"

zip saves_$(date +%Y-%m-%d_%H%M%S).zip "$dir"/Vault?.sav{,.bkp}
