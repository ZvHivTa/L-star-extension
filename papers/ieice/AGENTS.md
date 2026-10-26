# IEICE manuscript instructions

## Scope and independence

- This directory is the primary manuscript project. Keep it self-contained;
  it must compile after a fresh clone without Python or experimental outputs.
- The only manuscript entry point is `ieice_draft.tex` in this directory.
- Compile here with `latexmk -pdf ieice_draft.tex`, or from the repository root
  with `latexmk -cd -pdf -outdir=build papers/ieice/ieice_draft.tex`.
- Put every generated file in this directory's `build/`. Do not commit build
  products, previews, temporary scripts, or intermediate files.
- Keep editor configuration usable when opening this directory independently
  and when opening the repository root. Preserve paper-local bibliography and
  class/style dependencies.
- Do not change experiment code or results as part of manuscript-only edits.

## Immutable reference template

The original `ieice-tecrep_v1.1/` reference directory remains outside this
repository in the original local paper directory. It was not migrated and is
not a build dependency. Never edit, format, overwrite, move, rename, delete,
clean, or compile the original reference directory or its contents, including
`__MACOSX/`. Read-only comparison is permitted. The same protection applies if
a reference template directory is separately made available on another machine.
Make authorized changes only to the manuscript's working `.cls`/`.bst` copies.
