# Cinder
Project for COMP333  
Chvoong24: Chris Voong  
duyhuynh-dev: Duy Huynh  
bentaffet: Ben Taffet  
Hawklight1: Ben Mckinney 
https://github.com/Chvoong24/Cinder/blob/main/README.md


# Table Of Contents
- [Start Up](#start-up)
    - [Create An Enviroment](#create-a-python-enviroment)
    - [Necessary Imports](#imports)
- [How To Use](#how-to-fetch-data)
- [How Do You Know It Works](#how-do-you-know-it-works-unit-tests)

## Start Up
1. Clone Repository 
> Instructions For VSCode IDE
#### Create A Python Enviroment
1. Windows: Ctrl + Shift + P  
   Mac: Cmd + Shift + P  

0. Select: ``Python: Create Enviroment...``
0. Select: ``Venv`` or ``Conda`` (If you have Conda enviroments set up)
0. Select: ``Python 3.13.x``
0. Open a new Terminal Window
0. Terminal Line should say ``(.venv) (base)...``

## Imports
1. Import requests with ``pip install requests`` in VSCode terminal


## How To Fetch Data
1. Go to the **fetch_all.py** file
2. Run file
3. Wait for completion checks in IDE terminal (may take a while)
4. Files appear in ```<model>_download```. Logs appear in ```<model>_log``` folder

>Note: You can interrupt the fetch data process whenever you feel like it after you run the file

## How To Interrupt Data Fetch
1. For VSCode: Press ```Ctrl``` + ``` C ``` until terminal stops printing

## How Do You Know It Works? (Unit Tests)
1. Run ```fetch_all.py```
0. Go into repository directory
0. *If* ```<model>_data``` exists and contains ```<model>_download``` and ```<model>_logs```, it passes unit test
0. *If not*, it has failed

## Documentation
Documentation for all functions can be found at ```build/html/index.html```. It is still work in progress.
