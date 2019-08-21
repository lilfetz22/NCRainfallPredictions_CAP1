#!/bin/bash
#
# FILE: configure_admin.sh
#=========================================
# Configures admin user account
# 
# Prereq: must be run as root
#=========================================

echo "[CONFIGURE_ADMIN] Set admin password."
cat ./.admin.secret | chpasswd
