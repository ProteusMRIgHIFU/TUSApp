function Trans = generateH317Trans(varargin)

    Trans = varargin{1};
    if ~isfield(Trans,'frequency'), Trans.frequency = 0.2; end % nominal frequency in MHz
    % Vantage:  5.208 is closest supported frequency to 5 MHz
    if ~isfield(Trans,'Bandwidth'), Trans.Bandwidth = [0.7, 0.9]; end    	% 250 KHz frequency
    Trans.name = 'custom';
    Trans.id = 0;                      % find from the scanner head
    Trans.type = 2;                     % 2D transducer
    Trans.connType = 1; %  HDI 260-ZIF
    Trans.units = 'wavelengths';
    Trans.numelements = 128;            % no of transducer element
    Trans.elementWidth = 9.5;              % width of the element in mm or wavelengths
    Trans.spacingMm = Trans.elementWidth/0.9;                 % guess
    Trans.elevationApertureMm = Trans.spacingMm;
    
    Trans.radiusMm = 135;

    Trans.ElementPos = zeros(Trans.numelements,5);
    arraygeom = computeH317Geometry; % Get the x,y,z coordinates (from the test stat)
%     arraygeom(1:128, 3) = Trans.radiusMm - sqrt(Trans.radiusMm^2 - ((arraygeom(1:128, 1).^2 + arraygeom(1:128, 2).^2))); % z = r-sqrt(r^2 -sqsrt(x^2+y^2))
    Trans.ElementPos = arraygeom;
    Trans.ElementPos(1:128, 4) = atan(arraygeom(:,1) ./ (Trans.radiusMm-arraygeom(:,3)) ); % AZ = atan(x/z)
    Trans.ElementPos(1:128, 5) = atan(arraygeom(:,2) ./ sqrt( arraygeom(:,1).^2 + (Trans.radiusMm-arraygeom(:,3)).^2 ) ); % EL = atan(y/sqrt(x^2+z^2)), where z has to be wrt geometric focus.
    
    % --- from SCI Test Report for H-313
    Trans.maxAvgPower = 10;   % Watts
    Trans.impedance = 50;      % Ohms
    Trans.maxHighVoltage = 50;  % sqrt(100*Trans.impedance) = 100 = sqrt(Pmax*Z)
    Trans.lensCorrection = 0;   % guess
    
    % Trans.ElementSens = ;
    Trans.ConnectorES= [49, 34, 33, 17, 2, 1,113, 98, 97, 81, 66, 65, 50, 51, 35, 36, 18, 19, 3, 4, 114, ...
        115, 99, 100, 82, 83, 67, 68, 52, 53, 54, 37, 38, 39, 40, 20, 23, 21, 22, 5, 6, 7, 8, 116, 117, 118, ...
        101, 102, 103, 104, 84, 85, 86, 69, 70, 71, 72, 55, 56, 57, 41, 42, 43, 44, 26, 24, 25, 9, 10, 11, ...
        12, 122, 119, 120, 121, 105, 106, 107, 108, 90, 87, 88, 89, 73, 74, 75, 76, 58, 59, 62, 63, 64, 45, ...
        46, 47, 48, 28, 27, 29, 30, 31, 32, 13, 14, 15, 16, 124, 125, 123, 126, 127, 128, 109, 110, 111, 112, ...
        92, 93, 91, 94, 95, 96, 77, 78, 79, 80, 60, 61]';

    speedOfSound = 1.540;  % default speed of sound in mm/usec
    
    % Set a conservative value for maxHighVoltage, if not already defined
    if ~isfield(Trans,'maxHighVoltage'), Trans.maxHighVoltage = 50; end

    % Now convert all units as required, based on Trans.units
    scaleToWvl = Trans.frequency/speedOfSound; % conversion factor from mm to wavelengths

    % regardless of units, always provide spacing and radius in
    % wavelengths if they have been defined
    if isfield(Trans, 'spacingMm') && ~isempty(Trans.spacingMm)
        Trans.spacing = Trans.spacingMm * scaleToWvl;   % Spacing between elements in wavelengths.
    end
    if  isfield(Trans, 'radiusMm') && ~isempty(Trans.radiusMm)
        Trans.radius = Trans.radiusMm * scaleToWvl; % convert radiusMm to wavelengths
    end

    % define Trans.ElementSens based on Trans.elementWidth, but only if
    % user has not already defined it; assign default elementWidth if
    % it doesn't exist or is empty
    if ~isfield(Trans,'ElementSens')
        % Set element sensitivity function (101 weighting values from -pi/2 to pi/2).
        if ~isfield(Trans,'elementWidth') || isempty(Trans.elementWidth)
            % create default value of zero if not assigned in case
            % statements above (zero implies the element is a point
            % source)
            Trans.elementWidth = 0;
        end
        Theta = (-pi/2:pi/100:pi/2);
        Theta(51) = 0.0000001; % set to almost zero to avoid divide by zero.
        % note at this point elementWidth is in mm, so we have to
        % convert to wavelengths for the ElementSens calculation
        eleWidthWl = Trans.elementWidth * scaleToWvl;
        if eleWidthWl < 0.01
            % avoid the divide by zero for very small values (in this
            % case the sinc function will be extremely close to 1.0 for
            % all Theta, so we only need the cos term)
            Trans.ElementSens = abs(cos(Theta));
        else
            Trans.ElementSens = abs(cos(Theta).*(sin(eleWidthWl*pi*sin(Theta))./(eleWidthWl*pi*sin(Theta))));
        end
    end


    if strcmp(Trans.units, 'wavelengths')
        % convert all mm unit variables to wavelengths.  Note columns 4
        % and 5 of the ElementPos array are angles in radians, and do
        % not require units conversion
        Trans.elementWidth = Trans.elementWidth * scaleToWvl;
        Trans.ElementPos(:,1) = Trans.ElementPos(:,1) * scaleToWvl;
        Trans.ElementPos(:,2) = Trans.ElementPos(:,2) * scaleToWvl;
        Trans.ElementPos(:,3) = Trans.ElementPos(:,3) * scaleToWvl;
        if Trans.type == 3
            % for type 3 annular arrays, the fourth column is also a distance, not an angle
            Trans.ElementPos(:,4) = Trans.ElementPos(:,4) * scaleToWvl;
        end
        Trans.lensCorrection = Trans.lensCorrection * scaleToWvl;
    end
    

end