# Cinder
Project for COMP333  

# Table Of Contents
- [Members](#members)
- [Start Up](#start-up)
    - [Create An Enviroment](#create-a-python-enviroment)
    - [Necessary Imports](#imports)
- [How To Use](#how-to-fetch-data)
- [How Do You Know It Works](#how-do-you-know-it-works-unit-tests)
- [Run Local Website](#starting-local-website)


## Members
Chvoong24: Chris Voong  
duyhuynh-dev: Duy Huynh  
bentaffet: Ben Taffet  
Hawklight1: Ben Mckinney 

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

## Documentation
Documentation for all functions can be found at ```build/html/index.html```. It is still work in progress.  
A list of current issues and the state of the project can be found on our [Trello Board](https://trello.com/invite/b/68e3da706221ff22901d141c/ATTI9234f181668ee06c796b682eeee9fb732B0B90BF/team-cinder).

## Starting Local Website 
1. [Download MongoDB Community](https://www.mongodb.com/docs/manual/administration/install-community/?operating-system=macos&macos-installation-method=homebrew)
    - Choose your OS and follow download instructions

0. In your terminal, change directory until you are in backend
    - ```.../where/your/file/is/backend```
    1. ```terminal 
        cd .../Cinder/cinder-app/backend
        ```
    2. run ```npm run dev``` in your terminal

0. In a **new** terminal, change directory until you are in frontend/cinderWeb
    - ```.../where/your/file/is/frontend/cinderWeb```
    1. ```terminal
       cd .../Cinder/cinder-app/frontend/cinderWeb
       ```
    2. run ```npm run dev``` in your terminal

0. Go to localhost that was printed in frontend terminal on a browser

