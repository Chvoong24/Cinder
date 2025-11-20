#!/bin/bash

SCRIPT_PATH="/Cinder/fetch_all.py"
PYTHON_PATH="/usr/bin/python3"

CRON_JOB="0 */6 * * * $PYTHON_PATH $SCRIPT_PATH"

( crontab -l 2>/dev/null | grep -Fv "$SCRIPT_PATH" ; echo "$CRON_JOB" ) | crontab -