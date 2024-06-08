function AppUpdateDeliveryParameters(app)
%   AppUpdateDeliveryParameters - external function to control parameters
%   in LIFUControl application.
%   We use external functions outside the app as the app is a binary file
%   difficult to track changes in Github
%
% ABOUT:
%     author        - Samuel Pichardo
%     date          - Nov 22, 2021
%     last update   - Nov 22, 2021
%
    app.DutyCycleDropDown.UserData=str2double(app.DutyCycleDropDown.Value)/100;
    app.PRFHzDropDown.UserData=str2double(app.PRFHzDropDown.Value);
    app.IsppaWcm2Spinner.UserData=app.IsppaWcm2Spinner.Value;
    app.Ispta.UserData=app.IsppaWcm2Spinner.UserData * app.DutyCycleDropDown.UserData ;% conversion to %
    app.Ispta.Text = sprintf('%4.2f',app.Ispta.UserData);
    app.NumberCycles.UserData=floor(app.DutyCycleDropDown.UserData*app.Config.USFrequency/app.PRFHzDropDown.UserData);
    app.NumberCycles.Text=sprintf('%i',app.NumberCycles.UserData);
    app.DurationsDropDown.UserData=str2double(app.DurationsDropDown.Value);
    
    Isppa=app.IsppaWcm2Spinner.UserData;
    DutyCycle=app.DutyCycleDropDown.UserData;
    PRF=app.PRFHzDropDown.UserData;
    
    SelIsspa=app.Config.IsspaReference;
    
    if strfind(app.FocaldiameterDropDown.Value,'Broad')
        Dataset=app.Config.LargeFocus;
        Lia = ismember(Dataset.Index,[DutyCycle,SelIsspa,PRF],'rows');
        Lia=find(Lia);
    else
        Dataset=app.Config.SingleFocus;
        Lia = ismember(Dataset.Index,[DutyCycle,SelIsspa],'rows');
        Lia=find(Lia);
    end
    
    IsppaRatio=Isppa/SelIsspa;
    PresRatio=sqrt(IsppaRatio);

    app.MechanicalIndex.UserData=Dataset.AllData{Lia}.MI*PresRatio;
    
    app.ThernalIndex.UserData=Dataset.AllData{Lia}.TI*IsppaRatio;
    app.ThermalIndexSkull.UserData=Dataset.AllData{Lia}.TIC*IsppaRatio;
    app.ThermalIndexSkin.UserData=Dataset.AllData{Lia}.TIS*IsppaRatio;
    
    app.MechanicalIndex.Text=sprintf('%3.2f',app.MechanicalIndex.UserData);
    app.ThernalIndex.Text=sprintf('%3.2f',app.ThernalIndex.UserData);
    app.ThermalIndexSkull.Text=sprintf('%3.2f',app.ThermalIndexSkull.UserData);
    app.ThermalIndexSkin.Text=sprintf('%3.2f',app.ThermalIndexSkin.UserData);
    UpdatePlots(app,Dataset,Lia,IsppaRatio);
    