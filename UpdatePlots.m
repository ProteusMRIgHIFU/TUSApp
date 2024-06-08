function   UpdatePlots(app,Dataset,Lia,IsppaRatio)
%  UpdatePlots Summary 
%  external function to update plots in 
%   in LIFUControl application.
%   We use external functions outside the app as the app is a binary file
%   difficult to track changes in Github
%
% ABOUT:
%     author        - Samuel Pichardo
%     date          - Nov 22, 2021
%     last update   - Nov 22, 2021
%

    
    cy=floor(size(Dataset.AllData{Lia}.p_map,1)/2)+1;
    
    DensityMap=Dataset.MaterialList.Density(squeeze(Dataset.MaterialMap)'+1);
    SoSMap=    Dataset.MaterialList.SoS    (squeeze(Dataset.MaterialMap)'+1);
    IntensityMap=(Dataset.AllData{Lia}.p_map').^2/2./DensityMap./SoSMap/1e4*IsppaRatio;
    Tmap=(Dataset.AllData{Lia}.MonitorSlice'-37.0)*IsppaRatio+37.0;
    if app.bFirstPlot==false
        set(app.hIntensityMap,'CData',IntensityMap);
        set(app.hThermalMap,'CData',Tmap);
    else
        app.hIntensityMap=imagesc(app.UIAxes,Dataset.x_vec,...
               Dataset.z_vec,...
               IntensityMap,...
                [0	,app.Config.MaxIsppa/app.Config.IsspaReference *...
                     app.Config.SingleFocus.AllData{end}.MaxIsppa]);
        hold(app.UIAxes);
        plot(app.UIAxes,0,app.Config.DepthLocation,'y+','MarkerSize',20);
        for n=[1,2]
            [B,L] = bwboundaries(squeeze(Dataset.MaterialMap==n)','noholes');
            for k = 1:length(B)
               boundary = B{k};
               plot(app.UIAxes,Dataset.x_vec(boundary(:,2)),...
                   Dataset.z_vec(boundary(:,1)), 'w:', 'LineWidth', 1);
            end
        end
        colormap(app.UIAxes,jet);
        colorbar(app.UIAxes);
        xlim(app.UIAxes,[min(Dataset.x_vec),max(Dataset.x_vec)]);
        ylim(app.UIAxes,[min(Dataset.z_vec),max(Dataset.z_vec)]);
        
        daspect(app.UIAxes,[1,1,1]);
        
        app.hThermalMap=imagesc(app.UIAxes2,Dataset.x_vec,...
            Dataset.z_vec,...
            Tmap,...
            [37	,(app.Config.MaxIsppa/app.Config.IsspaReference *...
                  (max(app.Config.SingleFocus.AllData{1}.MonitorSlice(:))-37.0))+37.0]);

        colormap(app.UIAxes2,jet);
        colorbar(app.UIAxes2);
        hold(app.UIAxes2);
        plot(app.UIAxes2,0.0,app.Config.DepthLocation,'y+','MarkerSize',20);

        for n=[1,2]
            [B,L] = bwboundaries(squeeze(Dataset.MaterialMap==n)','noholes');
            for k = 1:length(B)
               boundary = B{k};
               plot(app.UIAxes2,Dataset.x_vec(boundary(:,2)),...
                   Dataset.z_vec(boundary(:,1)), 'w:', 'LineWidth', 1);
            end
        end
        xlim(app.UIAxes2,[min(Dataset.x_vec),max(Dataset.x_vec)]);
        ylim(app.UIAxes2,[min(Dataset.z_vec),max(Dataset.z_vec)]);
        daspect(app.UIAxes2,[1,1,1]);
        app.bFirstPlot = false;
    end

    
