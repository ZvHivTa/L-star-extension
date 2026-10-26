$pdf_mode = 1;
@default_files = ('ieice_draft.tex');
$out_dir = 'build';
$aux_dir = $out_dir;
$pdflatex = 'pdflatex -interaction=nonstopmode -halt-on-error %O %S';
