# User Readme

## Table of Contents
1. [Set up Cycle Downloading]()

## Cycle Downloading
> This only works for mac
- Get path to fetch_all.py
  - Open your a terminal window
  - Locate fetch_all.py in the main Cinder folder.
  - Drag the file from Finder and drop it directly into the Terminal window.
  - The full path to the file will automatically be inserted at the cursor's current position.
- Copy the script below and paste it into your terminal: ```SCRIPT_PATH="/path/to/your_script.py"
PYTHON_PATH=$(which python3) 
CRON_JOB="0 */6 * * * $PYTHON_PATH $SCRIPT_PATH" 
( crontab -l 2>/dev/null | grep -Fv "$SCRIPT_PATH" ; echo "$CRON_JOB" ) | crontab -```

- Replace ```"/path/to/your_script.py"``` with the path you got for fetch_all.py
- Click "Enter/Return"
- Type ```crontab -l``` into your termninal to check if it is there.
- type ```crontab -r``` to remove the cron.
