function [Params] = DefaultConfig(app,IDLabel)
%  DEFAULTCONFIG Summary 
%  To provide default config params
%  If you change this once the study starts, please comment the old with the
%  date, and be sure of making a commit!!!
%
% ABOUT:
%     author        - Samuel Pichardo
%     date          - Nov 8, 2021
%     last update   - Nov 22, 2021
    if ~exist('PathData.txt','file')
        errordlg("Please specify a PathData.txt indicating path to location of subject data...");
        Params=[];
        return
    end
    fid = fopen('PathData.txt');
    PathData = fgetl(fid);
    fclose(fid);
    PathData=strtrim(PathData);
    if ~exist(PathData,'dir')
        errordlg("The pathdata does not exists "+string(PathData));
        Params=[];
        return
    end
    Params.USFrequency = 700e3; % in Hz
%     Params.DepthLocation = 28.5; % Position in domain of target, mm
%     Params.DeviceLocation = 33.5; % Position in domain of target, mm
    Params.PRFValues= {'500','750','1000','1250'};% in Hz
    Params.DutyCyleValues={'3.5'};% in %
    Params.StimulationTimes= {'40'};% in s
    Params.MinIsppa= 0.0; %in W/cm2
    Params.MaxIsppa= 30; %in W/cm2
    Params.IsspaReference = 4.0; %in W/cm2
    Params.DepthLocation = 135.0 ;
    Params.UsingRefocus = false;
    
    if Params.UsingRefocus
         Infix='_9PPW_DataForSim';
         
    else
        Infix='_9PPW_TxMoved_DataForSim';
    end
    Params.DataDirectory=[PathData ,IDLabel]; %Location where protocols will be saved and executed
    if ~exist(Params.DataDirectory,'dir')
        errordlg(['Path for data does not exist ' ,Params.DataDirectory,'...closing app...'],'Data Path not found');
        Params= [];
        return
    end
    tfname=[Params.DataDirectory,filesep,'M1_700kHz_9PPW_TxMoved_DataForSim-ThermalField_AllCombinations.mat'];
    Params.SingleFocus=load(tfname);
    if ~isfield(Params.SingleFocus,'RatioLosses')
        errordlg("The field RatioLosses is not present in subject data single focus!! ");
        Params=[];
        return
    end
    tfname=[Params.DataDirectory,filesep,'M1_700kHz_9PPW_TxMoved_Test_Steer_ThermalField_AllCombinations.mat'];
    Params.LargeFocus=load(tfname);

end

