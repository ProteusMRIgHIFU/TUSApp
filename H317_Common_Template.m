% File name: H317_Common_Template.m
%%  Part 1 of TEMPLATE FOR ALL LIFU experiments (single and broad focus)
% matfilename,focustraversalfile, DutyCycle, PRF,Frequency parameters
% SelectedVoltage will be filled by the
% LIFU-APP

if bTestInTank
    res=questdlg("SCRIPT ONLY TO BE USED IN A TANK TEST. Continue?");
    if ~strcmp('Yes',res)
            msgbox("stopping protocol generation");
            error("Stopping protocol generation");
    end
end

MaxVoltage = 40;
MaxAvgPower= 410;
filename = ['MatFiles/', matfilename];

assert(SelectedVoltage<=MaxVoltage && SelectedVoltage >1.0 );
assert(TotalTime<=40.0 && TotalTime >0.0 );
assert(PRF==500.0 || PRF == 750.0 || PRF == 1000.0 || PRF ==1250.0);
assert(DutyCycle <=0.035);
assert(contains(matfilename,SubjectID));

assert(Frequency==7e5); % we only support 7e5 in this study

%% Procedure Parameters
LIFU.port = 'COM3'; % external power supply port
LIFU.PRF = PRF;  % Hz
LIFU.Duty = DutyCycle; % DutyCycle
LIFU.TransducerName = 'custom';
LIFU.Frequency = Frequency; % Hz
LIFU.MaxVoltage = MaxVoltage; % max voltage for operation. Change it once calibration is complete.
LIFU.Voltage = SelectedVoltage; % Operating voltage on startup
LIFU.TotalTime = TotalTime;

loadedFocusFile = load(focustraversalfile);
LIFU.FocalPoints = loadedFocusFile.ListPoints*1000; % in mm
LIFU.Phases = loadedFocusFile.PhasesReprogramPerPoint; % in radians
clear loadedFocusFile;

%% Define system parameters.
Resource.Parameters.Connector = 2; % connector no 2 for LIFU 
Resource.Parameters.numTransmit = 128;  % number of transmit channels.
Resource.Parameters.numRcvChannels = 128;  % number of receive channels.
Resource.Parameters.speedOfSound = 1540;
% Resource.Parameters.speedCorrectionFactor = 1.0;
Resource.Parameters.verbose = 3;
Resource.Parameters.initializeOnly = 0;
Resource.Parameters.simulateMode = 0;
%  Resource.Parameters.simulateMode = 1 forces simulate mode, even if hardware is present.
%  Resource.Parameters.simulateMode = 2 stops sequence and processes RcvData continuously.

%% Extenal power supply and TPC
Resource.HIFU.externalHifuPwr = 1;
Resource.HIFU.extPwrComPortID = LIFU.port;
Resource.HIFU.psType = 'QPX600DP'; % set to 'QPX600DP' or 'XG40-38' to match supply being used
Resource.HIFU.voltageTrackP5=5;
% TPC(5).maxHighVoltage = LIFU.MaxVoltage;
TPC(5).hv = LIFU.Voltage;

%% LIFU Parameters.
Trans.name = LIFU.TransducerName;
Trans.units = 'wavelengths';
Trans.frequency = LIFU.Frequency*1e-6; % frequency is in MHz
Trans.maxAvgPower=MaxAvgPower;
Trans.maxHighVoltage=MaxVoltage;
Trans = generateH317Trans(Trans); 

scaleToWvl = Trans.frequency/(Resource.Parameters.speedOfSound/1000);
%% TW structure
TW(1).type = 'parametric';
LIFU.PD = 1e3*LIFU.Duty/LIFU.PRF;% ms
C = LIFU.PD*1e3*Trans.frequency*2; % number of half cycles
TW(1).Parameters = [Trans.frequency,0.67,C,1];

if  contains(matfilename,'SingleFocus')
    %% Delay Calculation
    % No Delays
    Delay = zeros(1,Trans.numelements);

    %% Tx Structure

    TX(1).waveform = 1;            % use 1st TW structure.
    TX(1).Origin = [0.0,0.0,0.0];  % flash transmit origin at (0,0,0).
    TX(1).focus = 0; % focus distance
    TX(1).Steer = [0.0,0.0];       % theta, alpha = 0.
    TX(1).Apod = ones(1,Trans.numelements); % elements on
    TX(1).Delay = Delay;
    %% Specify SeqControl structure arrays. 
else
    Delay = [];
    for focalPointsCounter = 1:length(LIFU.FocalPoints)
        FocalPt = [LIFU.FocalPoints(focalPointsCounter,:) 135]*scaleToWvl;
        X = Trans.ElementPos(:,1)'- FocalPt(1);
        Y = Trans.ElementPos(:,2)' - FocalPt(2);
        Z = Trans.ElementPos(:,3)' - FocalPt(3);
        DelayTemp = sqrt(X.*X + Y.*Y + Z.*Z);
        Delay = [Delay; max(DelayTemp) - DelayTemp];
    end
    for focalPointsCounter = 1:length(LIFU.FocalPoints)
        TX(focalPointsCounter).waveform = 1;            % use 1st TW structure.
        TX(focalPointsCounter).Origin = [0.0,0.0,0.0];  % flash transmit origin at (0,0,0).
        TX(focalPointsCounter).focus = 0; % focus distance
        TX(focalPointsCounter).Steer = [0.0,0.0];       % theta, alpha = 0.
        TX(focalPointsCounter).Apod = ones(1,Trans.numelements); % elements on
        TX(focalPointsCounter).Delay = Delay(focalPointsCounter,:);
    end
end

if  contains(matfilename,'SingleFocus')
    nSteerFactor=1;
else % We try to do complete trajectories
    assert(contains(matfilename,'BroadFocus'));
    nSteerFactor=length(TX);
end

LIFU.Bursts = floor(LIFU.TotalTime/ (nSteerFactor/LIFU.PRF));

nsc=1;
TRIGGEROUT = nsc;
SeqControl(TRIGGEROUT).command = 'triggerOut';
nsc = nsc + 1;

TTNEB = nsc;
TTNALIFU = 1e6/LIFU.PRF;
SeqControl(TTNEB).command = 'timeToNextEB';
SeqControl(TTNEB).argument = TTNALIFU;
nsc = nsc + 1;

SYNC = nsc;
SeqControl(SYNC).command = 'sync';
nsc = nsc + 1;

RTNMatlab = nsc;
SeqControl(RTNMatlab).command = 'returnToMatlab';
nsc = nsc + 1;

%%%%%

SELTPC=nsc;
SeqControl(SELTPC).command = 'setTPCProfile';
SeqControl(SELTPC).argument = 5;
SeqControl(SELTPC).condition = 'immediate';
nsc = nsc + 1;

NOOPPRF=nsc;
SeqControl(NOOPPRF).command = 'noop';
SeqControl(NOOPPRF).argument = (1e6/PRF-LIFU.PD*1e3)*5; %1ms in steps of 0.2 us seconds
nsc = nsc + 1;

%%% Process
np=1;
TRACKPROCESS=np;
Process(TRACKPROCESS).classname = 'External';
Process(TRACKPROCESS).method = 'trackExposure';
Process(TRACKPROCESS).Parameters = {'srcbuffer','none',... % 
                        'dstbuffer','none'};      % no output buffer
np = np + 1;

PROCEND=np;
Process(PROCEND).classname = 'External';
Process(PROCEND).method = 'EndExposure';
Process(PROCEND).Parameters = {'srcbuffer','none',... % 
                        'dstbuffer','none'};      % no output buffer
np=np+1;
                    
%% Event Sequence
n = 1;
Event(n).info = 'select TPC profile 5';
Event(n).tx = 0;
Event(n).rcv = 0;
Event(n).recon = 0;
Event(n).process = 0;
Event(n).seqControl = SELTPC; % set TPC profile command.
n=n+1;

Event(n).info = 'NOOP';
Event(n).tx = 0;
Event(n).rcv = 0;
Event(n).recon = 0;
Event(n).process = 0;
Event(n).seqControl = NOOPPRF; %
n=n+1;
% EventPulse=n;

if  contains(matfilename,'SingleFocus')
    Event(n).info = 'LIFU Pulse';
    Event(n).tx = 1;
    Event(n).rcv = 0;
    Event(n).recon = 0;
    Event(n).process = 0;
    Event(n).seqControl = [RTNMatlab, TRIGGEROUT] ;
    n = n+1;
    
    EventPulse=n;
    
    Event(n).info = 'select TPC profile 5';
    Event(n).tx = 0;
    Event(n).rcv = 0;
    Event(n).recon = 0;
    Event(n).process = 0;
    Event(n).seqControl = SELTPC; % set TPC profile command.
    n=n+1;

    Event(n).info = 'NOOP';
    Event(n).tx = 0;
    Event(n).rcv = 0;
    Event(n).recon = 0;
    Event(n).process = 0;
    Event(n).seqControl = NOOPPRF; %
    n=n+1;
    
    Event(n).info = 'LIFU Pulse';
    Event(n).tx = 1;
    Event(n).rcv = 0;
    Event(n).recon = 0;
    Event(n).process = 0;
    Event(n).seqControl = [RTNMatlab] ;
    n = n+1;
    

else 
    for j=1:length(TX)
        Event(n).info = 'LIFU Pulse';
        Event(n).tx = j;
        Event(n).rcv = 0;
        Event(n).recon = 0;
        Event(n).process = 0;
        Event(n).seqControl = [RTNMatlab, TRIGGEROUT];
        n = n+1;
        if j<length(TX)-1
            Event(n).info = 'select TPC profile 5';
            Event(n).tx = 0;
            Event(n).rcv = 0;
            Event(n).recon = 0;
            Event(n).process = 0;
            Event(n).seqControl = SELTPC; % set TPC profile command.
            n=n+1;

            Event(n).info = 'NOOP';
            Event(n).tx = 0;
            Event(n).rcv = 0;
            Event(n).recon = 0;
            Event(n).process = 0;
            Event(n).seqControl = NOOPPRF; %
            n=n+1;
        end
    end
end

% EventPulse=n;
JUMP = nsc;
SeqControl(JUMP).command = 'jump';
SeqControl(JUMP).argument = EventPulse;

nsc = nsc + 1;

Event(n).info = 'Jump back to sonication';
Event(n).tx = 0;
Event(n).rcv = 0;
Event(n).recon = 0;
Event(n).process = TRACKPROCESS;
Event(n).seqControl = JUMP;
n=n+1;

Event(n).info = 'End of LIFU';
Event(n).tx = 0;
Event(n).rcv = 0;
Event(n).recon = 0;
Event(n).process = PROCEND;
Event(n).seqControl = RTNMatlab;

%we start VSX with LIFU disabled
Resource.Parameters.startEvent=n;

% %UI
UI(1).Control = {'UserB1','Style','VsPushButton','Label',...
    'Get ready!'};
UI(1).Callback=text2cell('%StartCallback');

% %UI
UI(2).Control = {'UserB2','Style','VsPushButton','Label',...
    'Sham'};
UI(2).Callback=text2cell('%ShamCallback');

%% Save Files
% Save all the structures to a .mat file.
global mainLIFUTimeLimit
global mainRunInTank
global OnlineSelVoltage
mainLIFUTimeLimit=TotalTime;
mainRunInTank=bTestInTank;
OnlineSelVoltage=SelectedVoltage;

save(filename);

return

%StartCallback
    global mainLIFUStartTime
    global OnlineSelVoltage
    mainLIFUStartTime=-1;
    pgn = get(hObject,'Value');
    curStartEvent=evalin('base','Resource.Parameters.startEvent');

    simulateMode=evalin('base','Resource.Parameters.simulateMode');
    Control = evalin('base', 'Control');
    Control.Command = 'set&Run';
    Control.Parameters = {'Parameters',1,'startEvent',1};
    evalin('base','Resource.Parameters.startEvent = 1;');
    assignin('base','Control',Control);
    
    if simulateMode==0
        fprintf('Hardware operation: We are setting the voltage monitor function\n');
        P5HVmin = OnlineSelVoltage*0.9;
        P5HVmax = OnlineSelVoltage*1.05;
        assignin('base', 'P5HVmax', P5HVmax);
        assignin('base', 'P5HVmin', P5HVmin);
        % call the function to set new limit values
        rc = setProfile5VoltageLimits(P5HVmin, P5HVmax);
        if ~strcmp(rc, 'Success')
            fprintf(2, ['Error from setProfile5VoltageLimits: ', rc, ' \n'])
        end
    else
        fprintf('Unable to set voltage monitor function as we are running in SW mode\n');
    
    end
%StartCallback

%ShamCallback
global mainLIFUTimeLimit
shamLIFUStartTime=tic;
mainNextTick=shamLIFUStartTime;
fLIFUbar=waitbar(0,sprintf('Sham progress - time to complete: %2.1f',mainLIFUTimeLimit));
while toc(shamLIFUStartTime)<mainLIFUTimeLimit
    curtTime=toc(shamLIFUStartTime); 
    s=sprintf('Sham progress - time to complete: %2.1f',mainLIFUTimeLimit-curtTime);
    waitbar(curtTime/mainLIFUTimeLimit,fLIFUbar,s);
    pause(1.0)
end
close(fLIFUbar);
tEnd = toc(shamLIFUStartTime)  ;
fprintf("Time to run %f\n",tEnd);
%ShamCallback