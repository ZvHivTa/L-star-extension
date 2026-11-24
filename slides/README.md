# Seminar TeX projects

本目录保存四次 seminar 幻灯片、中间发表文稿和本次 IEICE 会议幻灯片。
六个项目分别维护，
源码、图片和参考文献留在各自目录，所有编译产物写入该项目的 `build/`。

| 项目 | 类型 | 编译入口 | 生成文件 |
| --- | --- | --- | --- |
| `semi02` | Beamer / Madrid | `semi02/main.tex` | `semi02/build/main.pdf` |
| `semi03` | Beamer / Madrid | `semi03/main.tex` | `semi03/build/main.pdf` |
| `semi04` | Beamer / Madrid | `semi04/main.tex` | `semi04/build/main.pdf` |
| `semi05` | Beamer / Madrid | `semi05/main.tex` | `semi05/build/main.pdf` |
| `Tyukan` | A4 article 中间发表文稿 | `Tyukan/main.tex` | `Tyukan/build/main.pdf` |
| `ieice_slide` | Beamer / Madrid 会议幻灯片 | `ieice_slide/main.tex` | `ieice_slide/build/main.pdf` |

## 目录结构

```text
slides/
├── .latexmkrc
├── .gitignore
├── .vscode/settings.json
├── AGENTS.md
├── README.md
├── semi02/
├── semi03/
├── semi04/
├── semi05/
├── Tyukan/
└── ieice_slide/
```

每个子项目包含 `main.tex`、自己的 `.latexmkrc`、`.gitignore` 和
`.vscode/settings.json`。五个 Beamer 项目使用 `reference.bib`；
`Tyukan` 使用 `references.bib`。图片素材保留在原项目中。

`ieice_slide/` 是本次 IEICE 会议发表的工作项目，以 `semi05` 为起点，
复制其源码、参考文献及实际引用的图片，不复制历史预览图和编译产物。

## 编译

需要安装包含 pdfLaTeX、BibTeX、latexmk、Beamer、IEEEtran bibliography
样式及相关宏包的 TeX 发行版。无需 Python 实验环境。

在某个子项目目录运行：

```sh
latexmk -pdf main.tex
```

在 `slides/` 目录运行以下命令编译全部项目：

```sh
latexmk -pdf
```

也可只编译一个项目：

```sh
latexmk -pdf semi02/main.tex
```

在仓库根目录运行时，使用完整相对路径：

```sh
latexmk -pdf slides/semi02/main.tex
```

可在 VS Code 中打开仓库根目录、`slides/` 或任一子项目；LaTeX Workshop
均将 PDF 和中间文件输出到对应的 `build/`，包括 SyncTeX。
请使用 latexmk 或配置好的编辑器构建命令；直接运行 pdflatex 不会读取
`.latexmkrc` 中的输出路径设置。

## 生成文件

`build/` 已被 Git 忽略。旧的 `.aux`、`.fls`、`.nav`、`.snm`、日志等
不再与源码混放。只保留 PDF、清理中间文件时，在相应子项目运行：

```sh
latexmk -c main.tex
```

按用户要求，`ieice_slide/build/minecraft_syntactic_monoid_case_study.pdf`
是单独提交到 Git 的例外：它保存 Minecraft 简化案例的模型、最小 DFA、
syntactic monoid 和右 Cayley 图说明，没有保留独立 TeX 项目。
请在清理 `build/` 时保留这份辅助 PDF。

Beamer 项目使用 `\date{\today}`，重新编译时标题页会显示编译日期。
日常编译不额外生成截图或预览图。

## 历史排版提示

本次目录整理保留了历史文稿的正文与排版。四个 Beamer 项目仍有原来的
页脚标题超宽及部分页面内容溢出警告；`semi02` 的 `stern85` 文献条目还缺少
publisher 字段。这些警告不阻止生成 PDF，可在后续内容修订时单独处理。
