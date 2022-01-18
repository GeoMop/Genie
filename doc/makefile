all: documentation.md
	pandoc --toc --standalone --css air.css --mathjax -f markdown -t html --metadata pagetitle="Genie reference manual" documentation.md -o documentation.html
	pandoc --standalone -f markdown  -t latex documentation.md -o documentation.tex
	pdflatex documentation.tex
	
#--self-contained 
# As --self-contained does not work with mathjax, resolution is to replace <script ...>...MathJax.js</script>
# with:
# <script type="text/javascript" src="http://cdn.mathjax.org/mathjax/latest/MathJax.js"></script>
