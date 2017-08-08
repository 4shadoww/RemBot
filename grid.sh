#!/bin/bash

# Set time zone
export TZ="/usr/share/zoneinfo/Europe/Helsinki"

# Set locale
export LC_ALL="en_US.UTF-8"
export PYTHONIOENCODING="UTF-8"

# Start Rem
REM="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )/stabilizer.py"
$REM
exit $?
