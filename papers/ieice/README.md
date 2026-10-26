# IEICE 论文 LaTeX 项目

本目录是论文的主工作目录，与同一仓库内的 Python 实验项目独立编译。
论文标题为 *Extending the L-star Algorithm to Learn Syntactic Monoids*。

## 在另一台电脑上使用

首次使用时克隆仓库；已有仓库时，在切换电脑前提交并推送本机修改，
然后在另一台电脑拉取：

```sh
git clone https://github.com/ZvHivTa/L-star-extension.git
cd L-star-extension/papers/ieice
```

已有仓库时，在仓库中运行 `git pull --ff-only`，然后打开本目录。
请将论文修订提交到此目录，避免维护多个独立副本。

## 独立编辑与编译

安装 TeX Live（Windows 也需要 latexmk 可用的 Perl 环境）或其他包含
pdfLaTeX、BibTeX、latexmk 及所需宏包的 TeX 发行版。
在 VS Code 中安装 LaTeX Workshop，直接打开 `papers/ieice/` 即可编辑、
编译和预览。也可以打开整个仓库；仓库根目录提供了相同的 LaTeX 编译方案。

在本目录运行：

```sh
latexmk -pdf ieice_draft.tex
```

或在仓库根目录运行：

```sh
latexmk -cd -pdf -outdir=build papers/ieice/ieice_draft.tex
```

两种方式都将 PDF、中间文件及 SyncTeX 输出到本目录的 `build/`。
`build/` 不纳入 Git；另一台电脑首次编译时会自动创建。
直接运行不带输出目录参数的 `pdflatex` 不会读取 `.latexmkrc`，请使用上述命令。

本项目使用 graphicx、amsmath、newtxtext、newtxmath、booktabs、etoolbox、
cite、needspace 和 hyperref；完整 TeX Live 安装包含这些宏包。
BibTeX 使用随项目提供的 `ieicetr.bst`，无需 Python 环境或实验依赖。

## 文件

- `ieice_draft.tex`：唯一的论文编译入口。
- `references.bib`：参考文献库；通过 `\cite{...}` 引用，只打印实际引用的条目。
- `ieice-tecrep.cls`：IEICE Technical Report 文档类工作副本。
- `ieicetr.bst`：IEICE 配套发布的 BibTeX 样式，保留其来源说明。
- `.latexmkrc`：默认入口及 `build/` 输出目录。
- `.vscode/settings.json`：独立打开本目录时的 LaTeX Workshop 配置。
- `AGENTS.md`：后续编辑与编译约束。

## 原始模板

迁移时没有复制、移动或修改原始 `ieice-tecrep_v1.1/` 参照目录。
它保留在原电脑的旧论文目录中，本项目不依赖它，其他电脑无需该目录即可编译。
如需另行保存原始模板，应始终将其作为只读参照，不对它编译或生成产物。

文献样式来自 [IEICE 配套发布的样式包](https://www.ieice.org/ftp/tex/ieice/LaTeX2e/ieice_v2.3.zip)。
文档类、字体大小、纸张和双栏布局沿用会议模板；作者分隔符及命题环境的调整
保存在论文导言区。会议的页数、截止日期等要求仍需依据会议通知核对。

## Git 与实验隔离

实验输出与论文 `build/` 分开，论文可单独打开，不需要运行实验。
论文和代码共享仓库分支，切换分支、拉取和清理仓库前请先保存并提交修改。
提交论文时可指定路径，避免带入实验临时文件：

```sh
git add papers/ieice
git commit -m "Update IEICE manuscript"
git push
```

上述 Git 命令在仓库根目录运行。清理论文中间文件、保留 PDF 时，在本目录运行
`latexmk -c ieice_draft.tex`。
