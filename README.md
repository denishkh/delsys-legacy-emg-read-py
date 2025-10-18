# Read EMG, Accelerometer Data in Python from Delsys Trigno Legacy Sensor
This repository is a tutorial which shows how to read EMG/ACC data from delsys trigno legacy sensor. Code to plot different channel data is also provided. You can modify the code according to your requirement. It is successfully tested in Windows 11

## Setup Instructions
- Install Trigno SDK Server, which automaticallly installs Trigno Control Utility
- Connect the USB cable to PC, and connect the system to power.
- Connect the legacy sensors as many you want to collect data from.

- Open **Command Prompt as Administrator** and run:

```bash
dism /online /Enable-Feature /FeatureName:TelnetClient
```
This will install telnet client to your PC. It enables us to connect to devicecs over TCP/IP. <br>
- Type following to connect to the Delsys base
```
telnet 127.0.0.1 50040 
```
This should display the version number
Type following command and press enter two times
```
MASTER
```
This will set your system as master. and then following and press enter two times
 ```
 START
``` 
This will start data to stream to your port. You can listen to those port using python. <br> You can use different commands as given in  Page 6 and 7 of this User Manual. https://delsys.com/downloads/USERSGUIDE/trigno/sdk.pdf <br>

## Using read_emg_acc.py
- Provide channel number in this part of code which you want to plot and save
```
EMG_CHANNELS = [3, 5]   # list of EMG channels to plot (0-indexed)
IMU_CHANNELS = [3, 5]   # list of IMU channels to plot
```
Remember that this is zero indexed, you can modify the code if you want to start from 1. If you want to collect data from sensor 4, and 6, your list will look as shown above. <br>
You can add as many channel you want to.
-Run the code now, you will see a pop up window and real time plot. the axis range both EMG, and IMU can be adjusted from here
```
EMG_Y_RANGE = (-0.0001, 0.0001)
IMU_Y_RANGE = (-2, 2)

```



