function transxy = computeH317Geometry()
    T = readtable('H-317 XYZ Coordinates_double_corrected.csv');
    T_M =table2array(T);
    transxy = T_M(:,2:4)*25.4;
    transxy(:,3) = 135 - transxy(:,3);
end