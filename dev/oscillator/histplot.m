function h = histplot(datafile)

fid = fopen(datafile);
data = textscan(fid, '%s %s %f %d', 'Delimiter', ',', 'HeaderLines', 1);
fclose(fid);
h = data;

t = datenum(h{1}, 'mm/dd/yyyy HH:MM:SS');
p = h{3};
v = h{4};

% figure;
% subplot(2,1,1);
% plot(t,p);
% xlim([min(t), max(t)]);
% %hold on;
% subplot(2,1,2);
% plot(t,v);
% xlim([min(t), max(t)]);
% %set(gcf, 'XLim', [min(t), max(t)]);

figure;
[AX,~,~] = plotyy(t,p,t,v);
xlim(AX(1),[min(t), max(t)]);
xlim(AX(2),[min(t), max(t)]);