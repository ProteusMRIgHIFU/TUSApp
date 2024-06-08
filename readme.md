## Project Description

LIFUControl program is an application for generating protocol scripts supporting Transcranial Ultrasound Stimulation (TUS) at the University of Calgary. The program generates a python script file which can be used to operate 128 element phased-array transducer (H-317, [SonicConcepts](https://sonicconcepts.com/)) driven with with [Imaged Guided Therapy (IGT) system](http://www.imageguidedtherapy.com). The program uses acoustic simulations generated with [BabelBrain program](https://proteusmrighifu.github.io/BabelBrain/).

## Installation

Please download or clone the repository to your system and run LIFUControl.py file using python. It is recommended that a conda virtual environment [Anaconda](https://www.anaconda.com/) be used for installation of the python dependencies. 

## Requirements

Anaconda or miniconda: Virtual environment for python

Python packages: Python libraries required for running the application to create protocol scripts can be found in the "requirements.txt".

IGT library package: IGT system library to run the protocol script to operate the generator. Obtained throught IGT.

Babelbrain: Acoustic simulations

## Instructions for use

1. Open conda prompt activate your virtual environment.
2. Navigate to the LIFUControl directory.
3. Run the LIFUControl.py file.
    ```py
    python LIFUControl.py
    ```
4. Provide the following information on the dialog box in the following order.
    i. Participant ID
    ii. Operator Name
    iii. Location of your target (it is used as a prefix for simulation files from Babelbrain)
    iv. Change the simulation folder location (Master folder which includes all the simulation for all your participants)
    v. Hit ok
5. Select the correct parameters and intensity.
    i. Ensure that the Mechanical Index (MI) and Thermal Index (TI) are below the safety limits
6. Click on "Create IGT Script" or "Create IGT Sham Script" to create a active US or sham protocol.
    i. A graph with the intended pressure and free water pressure and protocol file location dialog box will appear
7. Open a new anaconda terminal and activate your virtual environment again.
8. Navigate to the created protocol folder.
9. Execute the protocol script using python.
    ```py
    python Run_TUS.py
    ```

## Contact

Samuel Pichardo, Ph.D\
Associate Professor\
Radiology and Clinical Neurosciences, Hotchkiss Brain Institute\
Cumming School of Medicine,\
University of Calgary\
samuel.pichardo@ucalgary.ca\
www.neurofus.ca