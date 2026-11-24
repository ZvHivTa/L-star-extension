$pdf_mode = 1;
$do_cd = 1;
@default_files = ('semi02/main.tex', 'semi03/main.tex', 'semi04/main.tex', 'semi05/main.tex', 'Tyukan/main.tex', 'ieice_slide/main.tex');
$out_dir = 'build';
$aux_dir = $out_dir;
$pdflatex = 'pdflatex -synctex=1 -interaction=nonstopmode -halt-on-error %O %S';
