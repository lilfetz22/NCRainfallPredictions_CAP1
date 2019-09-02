#!/bin/bash
#
# FILE: configure_admin.sh
#=========================================
# Configures admin user account
# 
# Prereq: must be run as root
#=========================================

if [ -f "$1" ]; then
	echo "[CONFIGURE_ADMIN] Set admin password."
	cat "$1" | chpasswd;
	rm -f "$1";		# remove password file 
else 
	echo >&2 "[CONFIGURE_ADMIN] Admin secret not found." && exit 1;
fi
