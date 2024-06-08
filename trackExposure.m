function trackExposure()
global mainLIFUTimeLimit
global mainLIFUStartTime
global mainRunInTank
global mainNextTick
global fLIFUbar
if mainRunInTank==false
    if mainLIFUStartTime==-1
        mainLIFUStartTime=tic;
        mainNextTick=mainLIFUStartTime;
        fLIFUbar=waitbar(0,sprintf('LIFU progress - time to complete: %2.1f',mainLIFUTimeLimit));
    else
        curtTime=toc(mainLIFUStartTime);
        if curtTime<mainLIFUTimeLimit
            curTick=toc(mainNextTick);
            if curTick>=5
                mainNextTick=tic;
                s=sprintf('LIFU progress - time to complete: %2.1f',mainLIFUTimeLimit-curtTime);
                waitbar(curtTime/mainLIFUTimeLimit,fLIFUbar,s);
            end
        else
            evalin('base','freeze=1;'); % this should stop
            if isvalid(fLIFUbar)
                close(fLIFUbar);
                tEnd = toc(mainLIFUStartTime)  ;
                fprintf("Time to run %f\n",tEnd);
            end

        end
    end
end
