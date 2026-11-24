$pdf_mode = 1;
$do_cd = 1;
@default_files = ('main.tex');
$out_dir = 'build';
$aux_dir = $out_dir;
$pdflatex = 'pdflatex -synctex=1 -interaction=nonstopmode -halt-on-error %O %S';
