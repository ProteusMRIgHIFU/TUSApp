function MI = MechanicalIndex(Isppa, Frequency)
%be sure of specifying peak intensity Isppa in W/cm2 and not the time-averaged  
% Frequency is in Hz
% We will use density and SoS of brain tissue
% Duck FA, Physical Properties of Tissue, Academic Press, London, 1990
    SoS = 1560; % m/
    Density = 1049; %kg/m3
    PressureMPA = sqrt(Isppa*1e4 * 2 * SoS * Density)/1e6;
    MI = PressureMPA / sqrt(Frequency/1e6);
end