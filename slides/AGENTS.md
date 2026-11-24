# Seminar TeX project instructions

- Each of `semi02`, `semi03`, `semi04`, `semi05`, `Tyukan`, and `ieice_slide` is an independent
  TeX project with `main.tex` as its only entry point.
- The seminar projects use Beamer; `Tyukan` uses the article class. Preserve
  their document classes, historical content, and local bibliography files.
- `ieice_slide` is the current IEICE conference presentation project, initially
  based on `semi05`; revise this project for the conference presentation.
- Keep image sources alongside the TeX source. Do not delete artwork merely
  because it is not referenced in the current document.
- Compile within a project using `latexmk -pdf main.tex`, from `slides/` using
  `latexmk -pdf semi02/main.tex` (adjust the project name), or from the repository
  root using `latexmk -pdf slides/semi02/main.tex`.
- Run `latexmk -pdf` within `slides/` to build all six projects.
- All PDFs, auxiliary files, SyncTeX files, build logs, and review images must
  be generated in each project's own `build/` directory. Do not commit ordinary
  build products.
- The user explicitly requested versioning
  `ieice_slide/build/minecraft_syntactic_monoid_case_study.pdf` as an exception.
  This is a preserved standalone supporting note with no retained TeX source;
  keep it tracked and do not remove it during build cleanup.
- Do not generate screenshots or review images unless the user requests them;
  use compile logs and PDF metadata for routine build checks.
- Maintain LaTeX Workshop settings for opening the repository root, `slides/`,
  or an individual project directory.
- Do not change experimental Python code or either paper project as part of
  seminar project maintenance.
