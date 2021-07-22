# ALMA
Analiza wyników ankiety losów absolwentów wydziału MIM.

## Generowanie analizy

- pandoc -f markdown writeup.md -s -o writeup.tex
- dodać \usepackage[margin=0.5in]{geometry} na początku latexa
- dodać colorlinks do hypersetup
- dodać \usepackage{float}
- zmienić \def\fps@figure{htbp} na {H}
- pdflatex writeup.tex

