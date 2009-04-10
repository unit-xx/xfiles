rem taskkill /im Acrobat.exe /fi "Windowtitle eq gcn_thesis.pdf*"
rem
xelatex gcn_thesis
bibtex gcn_thesis
xelatex gcn_thesis
xelatex gcn_thesis
