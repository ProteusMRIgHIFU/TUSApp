# This Python file uses the following encoding: utf-8
'''
LIFUContol: Application for the delivery of LIFU
ABOUT:
    author        - Samuel Pichardo
    date          - Feb 28, 2022
    last update   - Feb 28, 2022
'''

import os
from pathlib import Path
import sys
import numpy as np

from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout,QLineEdit,QDialog,
                QInputDialog, QMessageBox,QPushButton,QFileDialog,QTextEdit)
from PySide6.QtCore import QFile,Slot 
from PySide6.QtUiTools import QUiLoader
from PySide6.QtGui import QPalette

from scipy.io import loadmat
from H5pySimple import ReadFromH5py
from matplotlib.pyplot import cm
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import (
    FigureCanvas)
import cv2 as cv
import os
import sys
import shutil
from datetime import datetime
import yaml

def get_text_values(initial_texts, parent=None, title="", label=""):
    '''
    Input dialog box for selecting the patient imaging and simulation files

    Keyword arguments:
    initial_texts -- Last session data saved in an yaml file or placeholders
    parent -- parent object
    title -- dialog box title
    label -- prompt
    '''
    dialog = QInputDialog()
    dialog.setWindowTitle(title)
    dialog.setLabelText(label)
    dialog.show()
    # hide default QLineEdit
    dialog.findChild(QLineEdit).hide()

    editors = []
    for i, text in enumerate(initial_texts, start=1):
        if i == 5:
            editor = QTextEdit(text=text)
            editor.setDisabled(True)
            dialog.layout().insertWidget(i, editor)
        else:
            editor = QLineEdit(text=text)
            if i == 3:
                editor.setDisabled(True)
            dialog.layout().insertWidget(i, editor)
        editors.append(editor)
    chgePathDataBtn = QPushButton('Change Simulation Path')
    dialog.layout().insertWidget(len(editors)+1, chgePathDataBtn)
    chgePathDataBtn.clicked.connect(lambda: changePathData(editors[len(editors)-1]))

    ret = dialog.exec() == QDialog.Accepted
    returnStrings ={}
    returnStrings['ID'] = editors[0].text()
    returnStrings['ProjUser'] = editors[1].text()
    returnStrings['USFreq'] = editors[2].text()
    returnStrings['Prefix'] = editors[3].text()
    returnStrings['SimPath'] = editors[4].toPlainText()

    return ret, returnStrings

@Slot()
def changePathData(editor):
    '''
    Change the simulation file data

    Keyword arguments:
    editor -- RichTextEdit to display the new simulation folder
    '''
    SimPath = QFileDialog.getExistingDirectory(None,"Select a Directory",editor.toPlainText())
    # pathData = pathData.replace('/',os.sep)
    if SimPath != '':
        editor.setPlainText(SimPath)

###################################################################

class LIFUControl(QWidget):
    '''
    Main LIFU Control application

    '''
    def __init__(self):
        super(LIFUControl, self).__init__()
        self._bFirstPlot=True
        self.load_ui()
        self.InitApplication()

    def InitApplication(self):
        '''
        Initialization of GUI controls using configuration information

        '''

        # Get LastSession
        LastSessionfname = "LastSession.yml"

        EmptySessionVar = {}
        EmptySessionVar['ID'] = 'Enter ID Here'
        EmptySessionVar['ProjUser'] = 'Enter Project User Here'
        EmptySessionVar['USFreq']='250'
        EmptySessionVar['Prefix']='Enter Prefix Here'
        EmptySessionVar['SimPath']='Choose Simulation Folder'
        
        with open(LastSessionfname,'r') as f:
            LastSession = yaml.safe_load(f)
        
        if not isinstance(LastSession,dict) or len(LastSession) != 5:
            LastSession = {}
            LastSession['ID'] = EmptySessionVar['ID']
            LastSession['ProjUser'] = EmptySessionVar['ProjUser']
            LastSession['USFreq']=EmptySessionVar['USFreq']
            LastSession['Prefix']=EmptySessionVar['Prefix']
            LastSession['SimPath']=EmptySessionVar['SimPath']

        # Intialize with patient simulations
        prompt = 'ID of Patient (e.g. "ID001") and Name of Operator:'
        dlgtitle = 'LIFU Study'
        ret,inputs=get_text_values([LastSession['ID'],LastSession['ProjUser'], LastSession['USFreq'], LastSession['Prefix'], LastSession['SimPath']],title=dlgtitle,label=prompt)
        if not ret:
            msgBox = QMessageBox()
            msgBox.setText("User cancelling operation, closing app...")
            msgBox.exec()
            sys.exit(0)

        self.Widget.DateLabel.setText(datetime.now().strftime("%b %d, %Y"))

        self.Widget.IDLabel.setText(inputs['ID'])
        self.Widget.OperatorLabel.setText(inputs['ProjUser'])
        self.USFreq = inputs['USFreq']
        self.Prefix = inputs['Prefix']
        self.PathData = inputs['SimPath']

        if inputs['ID'] == EmptySessionVar['ID']and inputs['ProjUser'] ==EmptySessionVar['ProjUser'] and inputs['Prefix'] == EmptySessionVar['Prefix']:
            with open(LastSessionfname,'w') as f:
                yaml.dump(inputs,f)
            self.EndWithError("Please specify an ID, Project User and Prefix.")
        
        if not os.path.isdir(inputs['SimPath']):
            with open(LastSessionfname,'w') as f:
                yaml.dump(inputs,f)
            self.EndWithError("Please provide a valid folder for simulation files.")

        with open(LastSessionfname,'w') as f:
                yaml.dump(inputs,f)

        self.DefaultConfig(inputs['ID'])

        # Intialize widgets
        while self.Widget.FrequencyDropDown.count()>0:
            self.Widget.FrequencyDropDown.removeItem(0)
        self.Widget.FrequencyDropDown.insertItems(0, self.Config['USFrequency'])
    
        self.Widget.IsppaSpinBox.setRange(self.Config['MinIsppa'],self.Config['MaxIsppa'])
        self.Widget.IsppaSpinBox.setValue(self.Config['SingleFocus'][self.Widget.FrequencyDropDown.currentIndex()]['Index'][0][4])

        while self.Widget.ParamDropDown.count()>0:
            self.Widget.ParamDropDown.removeItem(0)
        self.Widget.ParamDropDown.insertItems(0, self.GetParamValues(self.Config['SingleFocus'][self.Widget.FrequencyDropDown.currentIndex()]))

        self.setWindowTitle('LIFU Delivery - Frequency = %i kHz' % (int(self.Widget.FrequencyDropDown.currentText())))

        # Widget callback connections
        self.Widget.FrequencyDropDown.currentIndexChanged.connect(self.UpdateParamsInt)
        self.Widget.ParamDropDown.currentIndexChanged.connect(self.UpdateParamsInt)
        # self.Widget.FocalDiameterDropDown.currentIndexChanged.connect(self.UpdateParamsFocus)
        self.Widget.IsppaSpinBox.valueChanged.connect(self.UpdateParamsFloat)
        self.Widget.PrepareVerasonicsScript.clicked.connect(self.PrepareVerasonicsScript)
        self.Widget.PrepareIGTScript.clicked.connect(self.PrepareIGTScript)
        self.Widget.PrepareIGTShamScript.clicked.connect(self.PrepareIGTShamScript)

        self.Widget.FrequencyDropDown.setDisabled(True)

        if self.USFreq == '250':
            self.Widget.FocalDiameterDropDown.setDisabled(True)

        # Update the GUI and control parameters
        self.UpdateDeliveryParameters()



    def UpdateDeliveryParameters(self):
        '''
        Update of GUI elements and parameters to be used in LIFU
        '''

        self.Widget.FrequencyDropDown.setProperty('UserData',float(self.Widget.FrequencyDropDown.currentText())*1e3)

        if 'Broad' in self.Widget.FocalDiameterDropDown.currentText():
            Dataset=self.Config['LargeFocus'][self.Widget.FrequencyDropDown.currentIndex()]
            Lia= self.Widget.ParamDropDown.currentIndex()            
        else:
            Dataset=self.Config['SingleFocus'][self.Widget.FrequencyDropDown.currentIndex()]
            Lia= self.Widget.ParamDropDown.currentIndex()  
        
        self.Widget.IsppaSpinBox.setProperty('UserData',self.Widget.IsppaSpinBox.value())
        
        Isppa=self.Widget.IsppaSpinBox.property('UserData')
        DutyCycle=Dataset['Index'][Lia][0]
        PRF=Dataset['Index'][Lia][1]

        self.Widget.IsptaLabel.setProperty('UserData',self.Widget.IsppaSpinBox.property('UserData')*DutyCycle)
        self.Widget.IsptaLabel.setText('%4.2f' % self.Widget.IsptaLabel.property('UserData'))

        SelIsspa=Dataset['Index'][Lia][4]
        self.Widget.NumberRepetitionsLabel.setProperty('UserData',np.floor((DutyCycle)*\
                                                                   (float(self.Widget.FrequencyDropDown.currentText())*1e3)/PRF))

        self.Widget.NumberRepetitionsLabel.setText('%i' % self.Widget.NumberRepetitionsLabel.property('UserData'))
        IsppaRatio=Isppa/SelIsspa
        PresRatio=np.sqrt(IsppaRatio)

        self.Widget.MILabel.setProperty('UserData',Dataset['AllData'][Lia]['MI']*PresRatio)
        self.Widget.TIBrainLabel.setProperty('UserData',Dataset['AllData'][Lia]['TI']*IsppaRatio)
        self.Widget.TICLabel.setProperty('UserData',Dataset['AllData'][Lia]['TIC']*IsppaRatio)
        self.Widget.TISkinLabel.setProperty('UserData',Dataset['AllData'][Lia]['TIS']*IsppaRatio)

        for obj in [self.Widget.MILabel,self.Widget.TIBrainLabel,self.Widget.TICLabel,self.Widget.TISkinLabel]:
            obj.setText('%3.2f' % obj.property('UserData'))

        CombParmStr = 'PRF: ' + str(PRF) +' Hz, ' + 'Duty Cycle: ' + str(DutyCycle) + '%, ' + '\nStimultion Duration: ' + str(Dataset['Index'][Lia][2]) + ' s'
        self.Widget.CombParamLabel.setText(CombParmStr)


        self.UpdatePlots(Dataset,Lia,IsppaRatio)

    def UpdatePlots(self,Dataset,Lia,IsppaRatio):
        '''
        Update of intensity and thermal maps plots

        Keyword arguments:
        Dataset -- BabelBrain stimulation (.h5 file)
        Lia -- Parameter selection from the simulation
        IsppaRatio -- Ratio between user defined Isppa and simulated Isppa
        '''
        IndexJ=Dataset['MaterialMap'].shape[1]//2
    
        DensityMap=Dataset['MaterialList']['Density'][Dataset['MaterialMap'][:,IndexJ,:]]
        SoSMap=    Dataset['MaterialList']['SoS'][Dataset['MaterialMap'][:,IndexJ,:]]
        IntensityMap=Dataset['AllData'][Lia]['p_map_central']**2/2/DensityMap/SoSMap/1e4*IsppaRatio
        Tmap=(Dataset['AllData'][Lia]['MonitorSlice']-37.0)*IsppaRatio+37.0

        if self._bFirstPlot:
            self._bFirstPlot=False

            extent=[Dataset['x_vec'].min(),Dataset['x_vec'].max(),Dataset['z_vec'].max(),Dataset['z_vec'].min()]
            MaxIsppa = IntensityMap.max()

            sr=['y:','w:']
            AllContours=[]
            for n in [1,2]:
               contours,_ = cv.findContours((Dataset['MaterialMap'][:,IndexJ,:]==n).astype(np.uint8), cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
               AllContours.append(contours)

            layout = QVBoxLayout(self.Widget.plot1)
            plt.rcParams['font.size']=8
            self._figIntensity=Figure(figsize=(7, 7))
            static_canvas = FigureCanvas(self._figIntensity)
            layout.addWidget(static_canvas)
            static_ax = static_canvas.figure.subplots()
            self._imIntensity=static_ax.imshow(IntensityMap.T,cmap=cm.jet,vmax=MaxIsppa,extent=extent)

            # Contours of skin and skull bone
            for n in range(2):
                contours=AllContours[n]
                for c in contours:
                    static_ax.plot(Dataset['x_vec'][c[:,0,1]],Dataset['z_vec'][c[:,0,0]],sr[n],linewidth=1)
            plt.colorbar(self._imIntensity,ax=static_ax)
            static_ax.set_title('Isppa (W/cm$^2$)')
            static_ax.set_xlabel('X (mm)')
            static_ax.set_ylabel('Z (mm)')
            self._figIntensity.tight_layout(pad=3)
            self._figIntensity.set_facecolor(np.array(self.palette().color(QPalette.Window).getRgb())/255)

            MaxTemp =Tmap.max()

            layout = QVBoxLayout(self.Widget.plot2)
            plt.rcParams['font.size']=8
            self._figTemp=Figure(figsize=(7, 7))
            static_canvas = FigureCanvas(self._figTemp)
            layout.addWidget(static_canvas)
            static_ax = static_canvas.figure.subplots()
            self._imTemperature=static_ax.imshow(Tmap.T,cmap=cm.jet,vmin=37.0,vmax=MaxTemp,extent=extent)
            # Contours of skin and skull bone
            for n in range(2):
                contours=AllContours[n]
                for c in contours:
                    static_ax.plot(Dataset['x_vec'][c[:,0,1]],Dataset['z_vec'][c[:,0,0]],sr[n],linewidth=1)
            plt.colorbar(self._imTemperature,ax=static_ax)
            static_ax.set_title('Temperature ($^{\circ}$C)')
            static_ax.set_xlabel('X (mm)')
            static_ax.set_ylabel('Z (mm)')
            self._figTemp.tight_layout(pad=3)
            self._figTemp.set_facecolor(np.array(self.palette().color(QPalette.Window).getRgb())/255)

        else:
            self._imIntensity.set_data(IntensityMap.T)
            self._imIntensity.set_clim(vmax=IntensityMap.max())
            self._figIntensity.canvas.draw_idle()
            self._imTemperature.set_data(Tmap.T)
            self._imTemperature.set_clim(vmax=Tmap.max())
            self._figTemp.canvas.draw_idle()



    def EndWithError(self,msg):
         '''
         Handle Errors

         Keyword arguments:
         msg -- Error message
         '''
         msgBox = QMessageBox()
         msgBox.setIcon(QMessageBox.Critical)
         msgBox.setText(msg)
         msgBox.exec()
         raise SystemError(msg)

    def DefaultConfig(self,IDLabel):
        '''
        Default configuration for the LIFU parameters and patient information

        Keyword arguments:
        IDLabel -- Patient ID
        '''
 
        PathData = self.PathData
        config={}

        config['USFrequency']       = [self.USFreq] # in KHz
        config['Prefix']            = self.Prefix
        config['MinIsppa']          = 0.1 #in W/cm2
        config['MaxIsppa']          = 30 #in W/cm2
        config['DepthLocation']     = 135.0 # in mm
        config['UsingRefocus']      = False
        config['SingleFocus']       = []
        config['LargeFocus']        = []


        # To be used for refocusing
        if config['UsingRefocus']:
            Infix='_6PPW_DataForSim' # changed from 9PPW to 6PPW
        else:
            Infix='_6PPW_TxMoved_DataForSim' # changed from 9PPW to 6PPW

        config['DataDirectory']=os.path.join(PathData ,IDLabel)# Location where protocols will be saved and executed
        config['DataDirectory'] = os.path.join(config['DataDirectory'] ,'m2m_' + IDLabel)
        if not os.path.isdir(config['DataDirectory']):
            self.EndWithError("The path data does not exist:\n["+config['DataDirectory']+"]")

        # Read BabelBrain simulation
        for idx, freq in enumerate(config['USFrequency']):
            if freq == '250':
                tfname = os.path.join(config['DataDirectory'], config['Prefix']+'_H317_'+freq+'kHz_6PPW_DataForSim-ThermalField_AllCombinations.h5')
            else:
                tfname = os.path.join(config['DataDirectory'],config['Prefix']+'_H317_'+freq+'kHz_6PPW_TxMoved_DataForSim-ThermalField_AllCombinations.h5')

            if not os.path.isfile(tfname):
                self.EndWithError("The input data does not exist:\n["+tfname+"]")
            config['SingleFocus'].append(ReadFromH5py(tfname))
            
            if 'RatioLosses' not in config['SingleFocus'][idx]:
                self.EndWithError("The field RatioLosses is not present in subject data single focus!!")
            
            if freq == '250':
                config['LargeFocus'].append(None)
            else:
                if not os.path.isfile(tfname):
                    self.EndWithError("The input data does not exist:\n["+tfname+"]")
                config['LargeFocus'].append(ReadFromH5py(tfname))

        self.Config=config

    def GetParamValues(self, stimFile):
        '''
        Simulated parameters as string for display

        Keyword arguments:
        stimFile -- stimulation dict
        '''
        IndexString = []
        for param in stimFile['Index']:
            tempString = 'PRF: ' + str(param[1]) + 'Hz,   ' + 'DC: ' + str(param[0]*100) + '%,   ' +'Stim Time: ' + str(param [2]) + ' s'
            IndexString.append(tempString)
        return IndexString

    def load_ui(self):
        '''
        Load form for gui
        '''
        loader = QUiLoader()
        path = os.fspath(Path(__file__).resolve().parent / "form.ui")
        ui_file = QFile(path)
        ui_file.open(QFile.ReadOnly)
        self.Widget = loader.load(ui_file, self)
        ui_file.close()


    @Slot(int)
    def UpdateParamsInt(self):
        self.UpdateDeliveryParameters()

    @Slot(float)
    def UpdateParamsFloat(self):
        self.UpdateDeliveryParameters()

    @Slot()
    def PrepareVerasonicsScript(self):
        '''
        Create protocol scripit for verasonics
        '''

        DesiredIsppa = self.Widget.IsppaSpinBox.property('UserData')
        Lia= self.Widget.ParamDropDown.currentIndex()  
        
        # Frequency=self.Config['USFrequency']
        Frequency=self.Widget.FrequencyDropDown.property('UserData')

        bTestInTank=self.Widget.TankTestcheckBox.isChecked()

        curdate=datetime.now()

        BroadFocus = 'Broad' in self.Widget.FocalDiameterDropDown.currentText()
        if BroadFocus:
            Infix="_BroadFocus"
            Dataset = self.Config['BroadFocus'][self.Widget.FrequencyDropDown.currentIndex()]
            DutyCycle= Dataset['Index'][Lia][0]
            PRF=Dataset['Index'][Lia][1]
            Duration=Dataset['Index'][Lia][2]
        else:
            Infix="_SingleFocus"
            Dataset = self.Config['SingleFocus'][self.Widget.FrequencyDropDown.currentIndex()]
            DutyCycle= Dataset['Index'][Lia][0]*100
            PRF=Dataset['Index'][Lia][1]
            Duration=Dataset['Index'][Lia][2]

        matfilename=self.Widget.IDLabel.text().replace("-","_")+ Infix+ "_"+curdate.strftime('%Y_%m_%d_T%H_%M_%S')

        matfilename=matfilename+"_DC%03i_PRF%i_Isppa%i" %(DutyCycle*1e3,PRF,DesiredIsppa*10)

        targetpath=self.Config['DataDirectory']+os.sep+"ProtocolFiles"
        if not os.path.isdir(targetpath):
            os.makedirs(targetpath)

        targetpath=targetpath+os.sep+matfilename
        if not os.path.isdir(targetpath):
            os.makedirs(targetpath)


        RatioLosses = self.Config['SingleFocus']['RatioLosses']
        Voltage=self.RequiredVoltageVerasonics(DesiredIsppa,RatioLosses)

        Outputfname=targetpath+os.sep+matfilename+'.m'
        with open(Outputfname,'w') as fout:
            fout.write("%s\n" % "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
            fout.write("%%%%%% [%s]\n" % matfilename)
            fout.write("%%%%%% Protocol for subject %s;\n" % self.Widget.IDLabel.text())
            fout.write("%%%%%%  DATE = %s\n" % str(curdate))
            fout.write("%%%%%%  Isspa = %3.2f\n" %DesiredIsppa)
            fout.write("%%%%%%  DC = %3.2f%%\n" % (DutyCycle*100))
            fout.write("%%%%%%  PRF = %i\n" % PRF)
            fout.write("%%%%%%  Duration = %3.1f\n" % Duration)
            fout.write("%%%%%%  Frequency = %3.1f\n" %Frequency)
            fout.write("%%%%%%  Estimated losses ratio (dB) = %3.2f\n" % (10*np.log10(RatioLosses)))
            fout.write("%%%%%%  Test in tank = %i\n" % bTestInTank)
            fout.write("%s\n" % "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
            fout.write("clear all;\n")
            fout.write("delete(instrfind)\n")
            fout.write("%s\n" % "%%%%%%%%%%INPUT PARAMETERS%%%%%%%%%%%%%%%%%")
            fout.write("SubjectID='%s';\n" % self.Widget.IDLabel.text().replace("-","_"))
            fout.write("matfilename='%s';\n" % matfilename)
            focustraversalfile="%s-PHASES_FOR_STEERING.mat"% self.Widget.IDLabel.text()
            fout.write("focustraversalfile = '%s';\n" %focustraversalfile)
            fout.write("SelectedVoltage =%3.1f;\n" % Voltage)
            fout.write("PRF =%i;\n" % PRF)
            fout.write("DutyCycle =%5.4f;\n" % DutyCycle)
            fout.write("Frequency =%G;\n" % Frequency)
            fout.write("TotalTime=%3.1f;\n" % Duration)
            fout.write("bTestInTank=%i;\n" % bTestInTank)
            fout.write("%s\n" % "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
            with open('H317_Common_Template.m','r') as fin:
                RestCode=fin.readlines()
            fout.writelines(RestCode)

            filestocopy=["H-317 XYZ Coordinates_double_corrected.csv",
                             "generateH317Trans.m",
                             "computeH317Geometry.m",
                             "trackExposure.m",
                             "EndExposure.m",
                              self.Config['DataDirectory']+os.sep+focustraversalfile]

            for f in filestocopy:
                try:
                    shutil.copy(f,targetpath+os.sep)
                except:
                    msgBox = QMessageBox()
                    msgBox.setIcon(QMessageBox.Critical)
                    msgBox.setText("Error when copying files, check command prompt for details")
                    msgBox.exec()
                    raise

            msgBox = QMessageBox()
            msgBox.setText('Protocol file created\n%s' %Outputfname)
            msgBox.exec()

    @Slot()
    def PrepareIGTScript(self):
        '''
        Create protocol script for IGT
        '''
        # Frequency=self.Config['USFrequency']
        Frequency=self.Widget.FrequencyDropDown.property('UserData')
        if Frequency == 700e3:
            maxAmplitudeAllowedHardware = 255
        elif Frequency == 250e3:
            maxAmplitudeAllowedHardware = 180
        else:
            maxAmplitudeAllowedHardware = 0

        curdate=datetime.now()
        bTestInTank=self.Widget.TankTestcheckBox.isChecked()
        DesiredIsppa = self.Widget.IsppaSpinBox.property('UserData')
        Lia= self.Widget.ParamDropDown.currentIndex()  

        curdate=datetime.now()

        BroadFocus = 'Broad' in self.Widget.FocalDiameterDropDown.currentText()
        if BroadFocus:
            Infix="_BroadFocus"
            Dataset = self.Config['BroadFocus'][self.Widget.FrequencyDropDown.currentIndex()]
            DutyCycle= Dataset['Index'][Lia][0]*100
            PRF=Dataset['Index'][Lia][1]
            Duration=Dataset['Index'][Lia][2]
        else:
            Infix="_SingleFocus"
            Dataset = self.Config['SingleFocus'][self.Widget.FrequencyDropDown.currentIndex()]
            DutyCycle= Dataset['Index'][Lia][0]*100
            PRF=Dataset['Index'][Lia][1]
            Duration=Dataset['Index'][Lia][2]

        pythonfilename=self.Widget.IDLabel.text().replace("-","_")+ Infix+ "_"+curdate.strftime('%Y_%m_%d_T%H_%M_%S')

        midfix = "_USFreq_%i_DC_%03i_PRF_%i_Duration_%i_Isppa_%i" %(Frequency/1e3,DutyCycle*10,PRF,Duration*10,DesiredIsppa*10)
        pythonfilename=pythonfilename+midfix

        targetpath=self.Config['DataDirectory']+os.sep+"ProtocolFilesIGT"
        if not os.path.isdir(targetpath):
            os.makedirs(targetpath)

        targetpath=targetpath+os.sep+pythonfilename
        if not os.path.isdir(targetpath):
            os.makedirs(targetpath)


        RatioLosses = self.Config['SingleFocus'][self.Widget.FrequencyDropDown.currentIndex()]['RatioLosses']
        Amplitude=self.RequiredAmplitudeIGT(DesiredIsppa,RatioLosses)


        Outputfname=targetpath+os.sep+'RUN_TUS.py'

        with open('IGT_Protcol_Template.py','r') as fin:
            RestCode=fin.readlines()

        with open(Outputfname,'w') as fout:
            for l in RestCode:
                fout.write(l+'\n')
                if '###PART1' in l :
                    break
            fout.write("%s\n" % "#################################")
            fout.write("###### [%s]\n" % pythonfilename)
            fout.write("###### Protocol for subject %s\n" % self.Widget.IDLabel.text())
            fout.write("######  DATE = %s\n" % str(curdate))
            fout.write("######  Isspa = %3.2f\n" %DesiredIsppa)
            fout.write("######  DC = %3.2f\n" % (DutyCycle))
            fout.write("######  PRF = %i\n" % PRF)
            fout.write("######  Duration = %3.1f\n" % Duration)
            fout.write("######  Frequency = %3.1f\n" %Frequency)
            fout.write("######  Estimated losses ratio (dB) = %3.2f\n" % (10*np.log10(RatioLosses)))
            fout.write("######  Test in tank = %i\n" % bTestInTank)
            fout.write("#################################")
            fout.write("######INPUT PARAMETERS############")
            fout.write("SubjectID = '%s'\n" % self.Widget.IDLabel.text().replace("-","_"))
            fout.write("pythonfilename = '%s'\n" % pythonfilename)
            fout.write("frequencyUS = %G\n" % Frequency)
            fout.write("PRF = %i\n" % PRF)
            fout.write("dutyCycle = %3.1f\n" % DutyCycle)
            fout.write("totalUSDuration = %3.1f\n" % Duration)
            fout.write("maxAmplitudeAllowedHardware=%i\n" % maxAmplitudeAllowedHardware)

            if Frequency == 250e3:
                tfname=os.path.join(self.Config['DataDirectory'],self.Config['Prefix']+'_H317_'+self.Widget.FrequencyDropDown.currentText()+'kHz_6PPW_DataForSim.h5')
            else:
                tfname=os.path.join(self.Config['DataDirectory'],self.Config['Prefix']+'_H317_'+self.Widget.FrequencyDropDown.currentText()+'kHz_6PPW_TxMoved_DataForSim.h5')


            if not os.path.isfile(tfname):
                self.EndWithError("The input data does not exist:\n["+tfname+"]")

            data = ReadFromH5py(tfname)
            zOffset = -1*data['ZSteering']*1000 # in mm (Simulation: Far-field is POSITIVE and Near-field is NEGATIVE  || Transdcuer: Far-field is NEGATIVE and Near-field is POSITIVE)
            points_mm = [[0,0.6495190528383290,zOffset],[0.75,-0.6495190528383290,zOffset],[-0.75,-0.6495190528383290,zOffset]]
            if BroadFocus == False:
                fout.write("amplitude =%3.1f\n" % Amplitude)
                fout.write("points_mm =[[0,0,%3.1f]]\n" % zOffset)
            else:
                # fout.write("amplitude = 0" + str((np.ones(128)*Amplitude).tolist())+'\n')
                fout.write("amplitude =%3.1f\n" % Amplitude)
                # fout.write("points_mm = " + str(points_mm) +"\n"% 0)
                fout.write("points_mm = [[0,0.6495190528383290,%3.2f],[0.75,-0.6495190528383290,%3.2f],[-0.75,-0.6495190528383290,%3.2f]] \n"% (zOffset, zOffset, zOffset))

            fout.write("timePerLocation=%3.1f\n" % 2)
            fout.write("#################################")

            bSecondPart=False
            for l in RestCode:
                if '###PART2' in l:
                    bSecondPart=True
                if bSecondPart:
                    fout.write(l+'\n')

            filestocopy=["utils.py",
                         "generator_Calgary_128.ini",
                         "transducer_Calgary_128.ini",
                         "transducerXYZ.py",
                         "H317Functions.py",
                         "H-317 XYZ Coordinates_double_corrected.csv"]

            fout.close()

            for f in filestocopy:
                try:
                    shutil.copy(f,targetpath+os.sep)
                except:
                    msgBox = QMessageBox()
                    msgBox.setIcon(QMessageBox.Critical)
                    msgBox.setText("Error when copying files, check command prompt for details")
                    msgBox.exec()
                    raise

            msgBox = QMessageBox()
            msgBox.setText('Protocol file created\n%s' %Outputfname)
            msgBox.exec()

    @Slot()
    def PrepareIGTShamScript(self):
        '''
        Create protocol script for IGT (sham)
        '''
        # Frequency=self.Config['USFrequency']
        Frequency=self.Widget.FrequencyDropDown.property('UserData')
        if Frequency == 700e3:
            maxAmplitudeAllowedHardware = 255
        elif Frequency == 250e3:
            maxAmplitudeAllowedHardware = 180
        else:
            maxAmplitudeAllowedHardware = 0

        curdate=datetime.now()

        DesiredIsppa = self.Widget.IsppaSpinBox.property('UserData')
        Lia= self.Widget.ParamDropDown.currentIndex()  
        bTestInTank=self.Widget.TankTestcheckBox.isChecked()
        curdate=datetime.now()

        BroadFocus = 'Broad' in self.Widget.FocalDiameterDropDown.currentText()
        if BroadFocus:
            Infix="_BroadFocus"
            Dataset = self.Config['BroadFocus'][self.Widget.FrequencyDropDown.currentIndex()]
            DutyCycle= Dataset['Index'][Lia][0]*100
            PRF=Dataset['Index'][Lia][1]
            Duration=Dataset['Index'][Lia][2]
        else:
            Infix="_SingleFocus"
            Dataset = self.Config['SingleFocus'][self.Widget.FrequencyDropDown.currentIndex()]
            DutyCycle= Dataset['Index'][Lia][0]*100
            PRF=Dataset['Index'][Lia][1]
            Duration=Dataset['Index'][Lia][2]

        pythonfilename=self.Widget.IDLabel.text().replace("-","_")+ Infix+ "_"+curdate.strftime('%Y_%m_%d_T%H_%M_%S')

        midfix = "_USFreq_%i_DC_%03i_PRF_%i_Duration_%i_Isppa_%i" %(Frequency/1e3,DutyCycle*10,PRF,Duration*10,DesiredIsppa*10)
        pythonfilename=pythonfilename+midfix+"_SHAM"

        targetpath=self.Config['DataDirectory']+os.sep+"ProtocolFilesIGT"
        if not os.path.isdir(targetpath):
            os.makedirs(targetpath)

        targetpath=targetpath+os.sep+pythonfilename
        if not os.path.isdir(targetpath):
            os.makedirs(targetpath)


        RatioLosses = self.Config['SingleFocus'][self.Widget.FrequencyDropDown.currentIndex()]['RatioLosses']
        Amplitude=self.RequiredAmplitudeIGT(DesiredIsppa,RatioLosses)

        Outputfname=targetpath+os.sep+'RUN_TUS.py'

        with open('IGT_Protcol_Sham_Template.py','r') as fin:
            RestCode=fin.readlines()

        with open(Outputfname,'w') as fout:
            for l in RestCode:
                fout.write(l+'\n')
                if '###PART1' in l :
                    break
            fout.write("%s\n" % "#################################")
            fout.write("###### SHAM ######### \n")
            fout.write("###### [%s]\n" % pythonfilename)
            fout.write("###### Protocol for subject %s\n" % self.Widget.IDLabel.text())
            fout.write("######  DATE = %s\n" % str(curdate))
            fout.write("######  Isspa = %3.2f\n" %DesiredIsppa)
            fout.write("######  DC = %3.2f\n" % (DutyCycle))
            fout.write("######  PRF = %i\n" % PRF)
            fout.write("######  Duration = %3.1f\n" % Duration)
            fout.write("######  Frequency = %3.1f\n" %Frequency)
            fout.write("######  Estimated losses ratio (dB) = %3.2f\n" % (10*np.log10(RatioLosses)))
            fout.write("######  Test in tank = %i\n" % bTestInTank)
            fout.write("#################################")
            fout.write("######INPUT PARAMETERS############")
            fout.write("SubjectID='%s'\n" % self.Widget.IDLabel.text().replace("-","_"))
            fout.write("pythonfilename='%s'\n" % pythonfilename)
            fout.write("frequencyUS =%G\n" % Frequency)
            fout.write("PRF =%i\n" % PRF)
            fout.write("dutyCycle =%3.1f\n" % DutyCycle)
            fout.write("totalUSDuration=%3.1f\n" % Duration)
            if BroadFocus == False:
                # fout.write("amplitude =%3.1f\n" % Amplitude)
                fout.write("amplitude =%3.1f\n" % 0)
                fout.write("points_mm =[[0,0,0]]\n" % Amplitude)
            else:
                # fout.write("amplitude =" + str((np.ones(128)*Amplitude).tolist())+'\n')
                fout.write("amplitude = " + str(0)+'\n')
                fout.write("points_mm =[[0,0.6495190528383290,0],[0.75,-0.6495190528383290,0],[-0.75,-0.6495190528383290,0]]\n" % Amplitude)

            fout.write("timePerLocation=%3.1f\n" % 2)
            fout.write("#################################")

            bSecondPart=False
            for l in RestCode:
                if '###PART2' in l:
                    bSecondPart=True
                if bSecondPart:
                    fout.write(l+'\n')

            fout.close()

            filestocopy=["utils.py",
                         "generator_Calgary_128.ini",
                         "transducer_Calgary_128.ini",
                         "transducerXYZ.py",
                         "H317Functions.py",
                         "H-317 XYZ Coordinates_double_corrected.csv"]

            for f in filestocopy:
                try:
                    shutil.copy(f,targetpath+os.sep)
                except:
                    msgBox = QMessageBox()
                    msgBox.setIcon(QMessageBox.Critical)
                    msgBox.setText("Error when copying files, check command prompt for details")
                    msgBox.exec()
                    raise

            msgBox = QMessageBox()
            msgBox.setText('Protocol file created\n%s' %Outputfname)
            msgBox.exec()

    def RequiredVoltageVerasonics(self,DesiredIsppa,RatioLosses):
        '''
        Input voltage for verasonics

        Keyword arguments:
        DesiredIsppa -- User defind Isppa
        RatioLosses -- Losses calulated with BabelBrain
        '''
        # Density and SoS of brain tissue
        # Duck FA, Physical Properties of Tissue, Academic Press, London, 1990
        SoS = 1560 # m/s
        Density = 1049 #kg/m3
        CalibrationData=loadmat('H317 IGT Amplitude Pressure Intensity ' + self.Widget.FrequencyDropDown.currentText() +' KHz.mat')
        CalibrationData['InputVoltage']=CalibrationData['InputVoltage'].flatten()
        CalibrationData['Pressure']=CalibrationData['Pressure'].flatten()
        CalibrationData['Intensity']=CalibrationData['Intensity'].flatten()
        AdjustedIsspa = DesiredIsppa/RatioLosses
        PressureMPA = np.sqrt(AdjustedIsspa*1e4 * 2 * SoS * Density)/1e6
        assert(PressureMPA>=np.min(CalibrationData['Pressure']) and PressureMPA<=np.max(CalibrationData['Pressure']))
        P=np.polyfit(CalibrationData['InputVoltage'],CalibrationData['Pressure'],1)
        #we just find the voltage we need
        SelVoltage=(PressureMPA-P[1])/P[0]
        fig=plt.figure()
        plt.subplot(1,2,1)
        plt.plot(CalibrationData['InputVoltage'],CalibrationData['Intensity'],'-+',linewidth=2,markersize=4)
        plt.title('Intensity Vs Voltage')
        plt.xlabel('V')
        plt.ylabel('W/cm2')
        plt.plot(SelVoltage,AdjustedIsspa,'s',markersize=14,markeredgecolor='r',markerfacecolor=[1, .6 ,.6,1])
        plt.plot(SelVoltage,DesiredIsppa,'s',markersize=14,markeredgecolor='r',markerfacecolor=[1, .6 ,.6,1])

        plt.subplot(1,2,2)
        plt.plot(CalibrationData['InputVoltage'],CalibrationData['Pressure'],'-+')
        P=np.polyfit(CalibrationData['InputVoltage'],CalibrationData['Pressure'],1)
        InV=np.linspace(0,40,100)
        p1d=np.poly1d(P)
        plt.plot(InV,p1d(InV),':',linewidth=2)
        plt.plot(SelVoltage,PressureMPA,'s',markersize=14,markeredgecolor='r',markerfacecolor=[1 ,.6, .6,1])
        plt.title('Pressure Vs Voltage')
        plt.xlabel('V')
        plt.ylabel('MPa')
        plt.show(block = False)
        return SelVoltage

    def RequiredAmplitudeIGT(self,DesiredIsppa,RatioLosses):
        '''
        Input amplitude for IGT

        Keyword arguments:
        DesiredIsppa -- User defind Isppa
        RatioLosses -- Losses calulated with BabelBrain
        '''
        # Density and SoS of brain tissue
        # Duck FA, Physical Properties of Tissue, Academic Press, London, 1990
        SoS = 1560 # m/s
        Density = 1049 #kg/m3
        currentFrequency = self.Widget.FrequencyDropDown.currentText()
        CalibrationData=loadmat('H317 IGT Amplitude Pressure Intensity ' + currentFrequency +' KHz.mat')
        CalibrationData['InputAmplitude']=CalibrationData['InputAmplitude'].flatten()
        CalibrationData['Pressure']=CalibrationData['Pressure'].flatten()
        CalibrationData['Intensity']=CalibrationData['Intensity'].flatten()
        AdjustedIsspa = DesiredIsppa/RatioLosses
        PressureMPA = np.sqrt(AdjustedIsspa*1e4 * 2 * SoS * Density)/1e6

        if not (PressureMPA>=np.min(CalibrationData['Pressure']) and PressureMPA<=np.max(CalibrationData['Pressure'])):
            self.EndWithError("Desired pressure (%f) beyond limits [%f, %f] of calibration " %(PressureMPA,np.min(CalibrationData['Pressure']),np.max(CalibrationData['Pressure'])))

        P=np.polyfit(CalibrationData['InputAmplitude'],CalibrationData['Pressure'],1)
        SelAmplitude=(PressureMPA-P[1])/P[0]
        if currentFrequency == '700':
            maxAmplitudeAllowed = 255
        elif currentFrequency == '250':
            maxAmplitudeAllowed = 180
        else:
            maxAmplitudeAllowed = 0
        if SelAmplitude>maxAmplitudeAllowed:
            SelAmplitude=maxAmplitudeAllowed
        elif SelAmplitude <0:
            SelAmplitude=0
        fig=plt.figure()
        plt.subplot(1,2,1)
        plt.plot(CalibrationData['InputAmplitude'],CalibrationData['Intensity'],'-+',linewidth=2,markersize=4)
        plt.title('Intensity Vs Amplitude')
        plt.xlabel('Amplitude')
        plt.ylabel('Intensity (W/cm2)')
        plt.plot(SelAmplitude,AdjustedIsspa,'s',markersize=14,markeredgecolor='r',markerfacecolor=[1, .6 ,.6,1])
        plt.plot(SelAmplitude,DesiredIsppa,'s',markersize=14,markeredgecolor='r',markerfacecolor=[1, .6 ,.6,1])

        plt.subplot(1,2,2)
        plt.plot(CalibrationData['InputAmplitude'],CalibrationData['Pressure'],'-+')
        P=np.polyfit(CalibrationData['InputAmplitude'],CalibrationData['Pressure'],1)
        InV=np.linspace(0,255,100)
        p1d=np.poly1d(P)
        plt.plot(InV,p1d(InV),':',linewidth=2)
        plt.plot(SelAmplitude,PressureMPA,'s',markersize=14,markeredgecolor='r',markerfacecolor=[1 ,.6, .6,1])
        plt.title('Pressure Vs Amplitude')
        plt.xlabel('Amplitude')
        plt.ylabel('Pressure (MPa)')
        plt.show(block = False)
        return SelAmplitude


if __name__ == "__main__":
    app = QApplication([])
    widget = LIFUControl()
    widget.show()
    sys.exit(app.exec())
