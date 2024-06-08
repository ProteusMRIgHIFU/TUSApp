function EndExposure()
global tractExposureTime
fprintf("end of exposure\n");
if ~isempty(tractExposureTime)
    totaltime=toc(tractExposureTime);
    fprintf("time for exposure =%f\n",totaltime);
end