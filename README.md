# Cinder
Project for COMP333  

# Table Of Contents
- [Members](#members)
- [System Requirements](#system-requirements)
- [Start Up](#start-up)
    - [Create An Enviroment](#create-a-python-enviroment)
    - [Necessary Imports](#imports)
- [How To Use](#how-to-fetch-data)
    - [More Info On Functions](#documentation)
- [How Do You Know It Works](#how-do-you-know-it-works-unit-tests)
- [Run Local Website](#starting-local-website)

- [Issues Tracker](#issues)

## Members
Chvoong24: Chris Voong  
duyhuynh-dev: Duy Huynh  
bentaffet: Ben Taffet  
Hawklight1: Ben Mckinney 

## System Requirements
Have at least 15GB of free storage

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

## Import Required Python Libraries
1. Ensure you are in the main "Cinder" directory.
2. In the terminal, run the command ``pip install -r requirements.txt``

# Table Of Contents
- [StyleGuide](#style-guide)
    - [Branching](#branching)
- [How To Use](#how-to-interrupt-data-fetch--end)

## How To Fetch Data
1. Go to the **fetch_all.py** file
0. Run file
0. Files appear in ```<model>_data```. In ```<model>_data``` download files appear in ```<model>_download``` folder. Logs appear in ```<model>_log``` folder.
0. Wait for completion checks in IDE terminal (may take a while)

>Note: You can interrupt the fetch data process whenever you feel like it after you run the file

## How To Interrupt Data Fetch
1. In the terminal window, press ```Ctrl``` + ``` C ``` until terminal stops printing

## How Do You Know It Works? (Unit Tests)
1. Run ```fetch_all.py```
0. Go into repository directory
0. *If* ```<model>_data``` exists and contains ```<model>_download``` and ```<model>_logs```, it passes unit test
0. *If not*, it has failed

## How to Visualize downloaded data
> This section is subject to change as we continue to improve and automate data collection and visualization.
1. Move the folder with the sitrep downloads into the grib_to_json folder. The folder will be called ```<model_download>``` as above. See visualization below for where to put the folder.  
&nbsp;a. You can do this by dragging files in your system directory or if you have the project open in VSCode.
```text
    /Cinder
    ├── Fetch_Scripts
    └── grib_to_json
         └── <sitrep>_download
```
2. In your terminal, run ```python grib_data_to_json.py```  
&nbsp;a. The script requires 3 arguments: a latitude, longitude and sitrep, in this order.  
&nbsp; To run the script correctly, use the following format: ```grib_data_to_json.py <lat> <lon> <sitrep>```.  
&nbsp;b. An example input for testing purposes could be ```grib_data_to_json.py 24.02619 -107.421197 href```. The only sitreps for now are "href", "nbm" and "refs".  
3. You should see a json file that appears in the ```grib_to_json``` folder.
4. In your terminal, run ```python forecast_json_parser.py```.  
&nbsp;a. The script requires 2 arguments: the name of the json file and a forecast hour from 0 to 48.  
&nbsp; To run the script correctly, use the following format: ```forecast_json_parser.py <json_filename> <forecast_hour>```.  
&nbsp; An example input for testing purposes could be ```forecast_json_parser.py href12z_for_24.02619,-107.421197.json 8```.  
5. You should see a printout with metadata and lines of probabalistic forecasts similar to the following:
```text
    Model: href
    Forecast time: 2025-10-16 12:00:00
    Location: {'lat': 24.02619, 'lon': -107.421197}
    Probability of > 12.7 kg m**-2 of Total Precipitation between 2025-10-16 19:00:00 and 2025-10-16 20:00:00 is 0.0
     ·
     ·
     ·
```
6. For now, there is a folder in grib_to_json called ```href_downloads``` which includes a sample href cycle download.  
There are also two sample json files that you can use to test ```forecast_json_parser.py```.



## Documentation
Documentation for all functions can be found at ```build/html/index.html```. It is still work in progress.  

## Issues
A list of current issues and the state of the project can be found on our [Trello Board](https://trello.com/invite/b/68e3da706221ff22901d141c/ATTI9234f181668ee06c796b682eeee9fb732B0B90BF/team-cinder).

## Starting Local Website 
1. [Download MongoDB Community](https://www.mongodb.com/docs/manual/administration/install-community/?operating-system=macos&macos-installation-method=homebrew)
    - Choose your OS and follow download instructions

0. In your terminal, change directory until you are in backend
    - ```.../where/your/file/is/backend```
    1. ```terminal 
        cd .../Cinder/cinder-app/backend
        ```
    0. Type ```npm install nodemon --save-dev``` in your terminal
    0. run ```npm run dev``` in your terminal

0. In a **new** terminal, change directory until you are in frontend/cinderWeb
    - ```.../where/your/file/is/frontend/cinderWeb```
    1. ```terminal
       cd .../Cinder/cinder-app/frontend/cinderWeb
       ```
    2. run ```npm run dev``` in your terminal

0. Go to localhost that was printed in frontend terminal on a browser

