function A=AreaH317()
    a=0.153/2; %half aperture, m
    r=0.135; %curvature radius, m
    theta=asin(a/r);
    c=cos(theta)*r;
    h=r-c;
    A=2*pi*r*h;
