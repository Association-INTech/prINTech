# Livrables

Générer un pdf à partir de .md (Markdown):
sudo apt install texlive-latex-recommended texlive-fonts-recommended
sudo apt install pandoc
pandoc [nom du fichier markdown].md -o [nom du fichier pdf à générer].pdf --toc -V geometry:margin=1in