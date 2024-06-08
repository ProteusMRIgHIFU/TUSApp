function PrepareProtocol(app)
%   AppUpdateDeliveryParameters - external function to prepare protocol to
%   execute with Verasonics
%   We use external functions outside the app as the app is a binary file
%   difficult to track changes in Github
%
% ABOUT:
%     author        - Samuel Pichardo
%     date          - Jan 29, 2022
%     last update   - Jan 29, 2022

    DesiredIsppa = app.IsppaWcm2Spinner.UserData;
    DutyCycle=app.DutyCycleDropDown.UserData;
    PRF=app.PRFHzDropDown.UserData;
    Duration=app.DurationsDropDown.UserData;
    Frequency=app.Config.USFrequency;
    bTestInTank=app.TanktestCheckBox.Value;
    curdate=now;

    BroadFocus=false;
    if strfind(app.FocaldiameterDropDown.Value,'Broad')
        BroadFocus=true;
    end

    if BroadFocus
        Infix="_BroadFocus";
    else
        Infix="_SingleFocus";
    end

    matfilename=strrep(app.IDLabel.Text,"-","_")+ Infix+ "_"+string(datestr(curdate,'yyyy_mm_dd_THH_MM_SS'));
    matfilename=matfilename+sprintf("_DC%03i_PRF%i_Isppa%i",DutyCycle*1e3,PRF,DesiredIsppa*10);
    targetpath=string(app.Config.DataDirectory)+filesep+"ProtocolFiles";
    if ~exist(targetpath,'dir')
        mkdir(targetpath);
    end
    targetpath=targetpath+filesep+matfilename;
    if ~exist(targetpath+filesep+'matFiles','dir')
        mkdir(targetpath+filesep+'matFiles');
    end
    
    RatioLosses = app.Config.SingleFocus.RatioLosses;
    Voltage=RequiredVoltage(DesiredIsppa,RatioLosses);
    %we wrote the parameters for the LIFU delivery
    Outputfname=targetpath+filesep+matfilename+'.m';
    fidOut=fopen(Outputfname,'w');
    fprintf(fidOut,"%s\n","%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%");
    fprintf(fidOut,"%%%%%% [%s]\n",matfilename);
    fprintf(fidOut,"%%%%%% Protocol for subject %s;\n",app.IDLabel.Text);
    fprintf(fidOut,"%%%%%%  DATE = %s\n",datestr(curdate));
    fprintf(fidOut,"%%%%%%  Isspa = %3.2f\n",DesiredIsppa);
    fprintf(fidOut,"%%%%%%  DC = %3.2f%%\n",DutyCycle*100);
    fprintf(fidOut,"%%%%%%  PRF = %i\n",PRF);
    fprintf(fidOut,"%%%%%%  Duration = %3.1f\n",Duration);
    fprintf(fidOut,"%%%%%%  Frequency = %3.1f\n",Frequency);
    fprintf(fidOut,"%%%%%%  Estimated losses ratio (dB) = %3.2f\n",10*log10(RatioLosses));
    fprintf(fidOut,"%%%%%%  Test in tank = %i\n",bTestInTank);
    fprintf(fidOut,"%s\n","%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%");
    fprintf(fidOut,"clear all;\n");
    fprintf(fidOut,"delete(instrfind);\n");
    fprintf(fidOut,"%s\n","%%%%%%%%%%INPUT PARAMETERS%%%%%%%%%%%%%%%%%");
    fprintf(fidOut,"SubjectID='%s';\n",strrep(app.IDLabel.Text,"-","_"));
    fprintf(fidOut,"matfilename='%s';\n",matfilename);
    focustraversalfile=sprintf("%s-PHASES_FOR_STEERING.mat",app.IDLabel.Text);
    fprintf(fidOut,"focustraversalfile = '%s';\n",focustraversalfile);
    fprintf(fidOut,"SelectedVoltage =%3.1f;\n",Voltage);
    fprintf(fidOut,"PRF =%i;\n",PRF);
    fprintf(fidOut,"DutyCycle =%5.4f;\n",DutyCycle);
    fprintf(fidOut,"Frequency =%G;\n",Frequency);
    fprintf(fidOut,"TotalTime=%3.1f;\n",Duration);
    fprintf(fidOut,"bTestInTank=%i;\n",bTestInTank);
    fprintf(fidOut,"%s\n","%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%");
    
    fidIn=fopen('H317_Common_Template.m','r');
    while(~feof(fidIn))
        s=fgetl(fidIn);
        fprintf(fidOut,"%s\n",s);
    end
    fclose(fidIn);
    fclose(fidOut);
    
    filestocopy=["H-317 XYZ Coordinates_double_corrected.csv",...
                 "generateH317Trans.m",...
                 "computeH317Geometry.m",...
                 "trackExposure.m",...
                 "EndExposure.m",...              
                 string(app.Config.DataDirectory)+filesep+focustraversalfile];
    for n =1:length(filestocopy)
        [status,msg]=copyfile(filestocopy(n),targetpath);
         if status ~=1
            errordlg(msg,"LIFUControl");
            return
         end
    end
    
    msgbox(sprintf('Protocol file create\n%s',Outputfname),'LIFUControl');



function Voltage=RequiredVoltage(DesiredIsppa,RatioLosses)
% We will use density and SoS of brain tissue
% Duck FA, Physical Properties of Tissue, Academic Press, London, 1990
    SoS = 1560; % m/
    Density = 1049; %kg/m3
    CalibrationData=load('H317 Voltage Pressure Intensity.mat');
    AdjustedIsspa = DesiredIsppa/RatioLosses;
    PressureMPA = sqrt(AdjustedIsspa*1e4 * 2 * SoS * Density)/1e6;
    assert(PressureMPA>=min(CalibrationData.Pressure) && PressureMPA<=max(CalibrationData.Pressure));
    [P,S]=polyfit(CalibrationData.InputVoltage,CalibrationData.Pressure,1);
    %we just find the voltage we need
    SelVotage=(PressureMPA-P(2))/P(1);
    figure;
    subplot(1,2,1);
    plot(CalibrationData.InputVoltage,CalibrationData.Intensity,'-+','LineWidth',2,'MarkerSize',4);
    title('Intensity Vs Voltage');
    xlabel('V');
    ylabel('W/cm2');
    hold on;
    plot(SelVotage,AdjustedIsspa,'s',MarkerSize=14,MarkerEdgeColor='red',...
    MarkerFaceColor=[1 .6 .6]);
    plot(SelVotage,DesiredIsppa,'s',MarkerSize=14,MarkerEdgeColor='red',...
    MarkerFaceColor=[1 .6 .6]);
    
    subplot(1,2,2);
    plot(CalibrationData.InputVoltage,CalibrationData.Pressure,'-+');
    [P,S]=polyfit(CalibrationData.InputVoltage,CalibrationData.Pressure,1);
    InV=linspace(0,40,100);
    hold on;
    plot(InV,polyval(P,InV),':','LineWidth',2);
    plot(SelVotage,PressureMPA,'s',MarkerSize=14,MarkerEdgeColor='red',...
    MarkerFaceColor=[1 .6 .6]);
    title('Pressure Vs Voltage');
    xlabel('V');
    ylabel('MPa');
    Voltage=SelVotage;
    