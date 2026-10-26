%%%
%% ieice-tecrep.cls 
%%  for IEICE Technical Report by ULS and Company, 2023. 
%% E-mail: ieice-div@uls.co.jp, teppei@uls.co.jp
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{ieice-tecrep}
%%[2023/09/25 v1.0 for IEICE Technical Report]
  [2023/11/21 v1.1 for IEICE Technical Report]

\def\tecrep@warning{\ClassWarningNoLine{ieice-tecrep}}

\newif\if@Proof \@Prooffalse
\DeclareOption{Proof}{\@Prooftrue}
\newif\if@cameraready \@camerareadyfalse
\DeclareOption{cameraready}{\@camerareadytrue}

\@ifundefined{@needsPformat}{}{%
 \edef\kenc@JYn{\cy@encoding}%
 \edef\kenc@JTn{\ct@encoding}%
}

\newcounter{@paper}
\newcommand{\@ptsize}{}
\newif\if@restonecol
\@ifundefined{hour}{}{%
 \hour\time \divide\hour by 60\relax
 \@tempcnta\hour \multiply\@tempcnta 60\relax
 \minute\time \advance\minute-\@tempcnta
}
\newif\if@enablejfam \@enablejfamtrue
\newif\if@mathrmmc \@mathrmmcfalse
\DeclareOption{a4paper}{\setcounter{@paper}{1}%
  \setlength\paperheight {297mm}%
  \setlength\paperwidth  {210mm}}
\DeclareOption{10pt}{\renewcommand{\@ptsize}{0}}
\DeclareOption{11pt}{\renewcommand{\@ptsize}{1}}
\DeclareOption{12pt}{\renewcommand{\@ptsize}{2}}
\@ifundefined{@needsPformat}{%
 \newif\iftombow
}{%
 \DeclareOption{tombow}{%
  \tombowtrue \tombowdatetrue
  \setlength{\@tombowwidth}{.1mm}%
  \@bannertoken{%
     \jobname\space:\space\number\year/\number\month/\number\day
      (\number\hour:\number\minute)}%
  \maketombowbox}%
 \DeclareOption{tombo}{%
  \tombowtrue \tombowdatefalse
  \setlength{\@tombowwidth}{.1mm}%
  \maketombowbox}%
 \DeclareOption{mentuke}{%
  \tombowtrue \tombowdatefalse
  \setlength{\@tombowwidth}{\z@}%
  \maketombowbox}%
 \DeclareOption{tate}{\AtBeginDocument{\tate\message{pLaTeX tate mode}}}%
}
\DeclareOption{oneside}{\@twosidefalse}
\DeclareOption{twoside}{\@twosidetrue}
\DeclareOption{onecolumn}{\@twocolumnfalse}
\DeclareOption{twocolumn}{\@twocolumntrue}
%%\DeclareOption{leqno}{\input{leqno.clo}}
\DeclareOption{fleqn}{\input{fleqn.clo}}
\DeclareOption{openbib}{%
  \AtEndOfPackage{%
   \renewcommand\@openbib@code{%
      \advance\leftmargin\bibindent
      \itemindent -\bibindent
      \listparindent \itemindent
      \parsep \z@
      }%
   \renewcommand\newblock{\par}}}
\@ifundefined{@needsPformat}{}{%
\DeclareOption{disablejfam}{\@enablejfamfalse}%
}
\DeclareOption{draft}{\setlength\overfullrule{5pt}}
\DeclareOption{final}{\setlength\overfullrule{0pt}}
\ExecuteOptions{a4paper,fleqn,twoside,twocolumn,final}
\ProcessOptions\relax

\@ifundefined{@needsPformat}{}{% kanjiskip
 \DeclareFontShape{\kenc@JYn}{mc}{m}{it}{<->ssub*mc/m/n}{}
 \DeclareFontShape{\kenc@JYn}{mc}{bx}{it}{<->ssub*gt/m/n}{}
 \DeclareFontShape{\kenc@JYn}{gt}{m}{it}{<->ssub*gt/m/n}{}
 \DeclareFontShape{\kenc@JYn}{gt}{bx}{it}{<->ssub*gt/m/n}{}
 \DeclareFontShape{\kenc@JYn}{mc}{b}{it}{<->ssub*mc/m/n}{}
 \DeclareFontShape{\kenc@JYn}{mc}{eb}{it}{<->ssub*mc/m/n}{}
 \DeclareFontShape{\kenc@JYn}{gt}{b}{it}{<->ssub*mc/m/n}{}
 \DeclareFontShape{\kenc@JYn}{gt}{eb}{it}{<->ssub*mc/m/n}{}
 \DeclareFontShape{\kenc@JYn}{gt}{ub}{it}{<->ssub*mc/m/n}{}
 \DeclareFontShape{\kenc@JYn}{mc}{m}{sc}{<->ssub*mc/m/n}{}
 \DeclareFontShape{\kenc@JYn}{mc}{m}{sl}{<->ssub*mc/m/n}{}
 %%
 \DeclareFontShape{\kenc@JTn}{mc}{m}{it}{<->ssub*mc/m/n}{}
 \DeclareFontShape{\kenc@JTn}{mc}{bx}{it}{<->ssub*gt/m/n}{}
 \DeclareFontShape{\kenc@JTn}{gt}{m}{it}{<->ssub*gt/m/n}{}
 \DeclareFontShape{\kenc@JTn}{gt}{bx}{it}{<->ssub*gt/m/n}{}
 \DeclareFontShape{\kenc@JTn}{mc}{b}{it}{<->ssub*mc/m/n}{}
 \DeclareFontShape{\kenc@JTn}{mc}{eb}{it}{<->ssub*mc/m/n}{}
 \DeclareFontShape{\kenc@JTn}{gt}{b}{it}{<->ssub*mc/m/n}{}
 \DeclareFontShape{\kenc@JTn}{gt}{eb}{it}{<->ssub*mc/m/n}{}
 \DeclareFontShape{\kenc@JTn}{gt}{ub}{it}{<->ssub*mc/m/n}{}
 \DeclareFontShape{\kenc@JTn}{mc}{m}{sc}{<->ssub*mc/m/n}{}
 \DeclareFontShape{\kenc@JTn}{mc}{m}{sl}{<->ssub*mc/m/n}{}
}

\renewcommand{\normalsize}{%
 \@setfontsize\normalsize\@ixpt{11\p@}%
 \abovedisplayskip 9\p@ \@plus 3\p@ \@minus 4\p@
 \abovedisplayshortskip \z@ \@plus 2.5\p@
 \belowdisplayshortskip 5\p@ \@plus 2\p@ \@minus 2\p@
  \belowdisplayskip \abovedisplayskip
  \let\@listi\@listI}
\normalsize
%\setbox0\hbox{\char\euc"A1A1}% "
%\setlength\Cht{\ht0}
%\setlength\Cdp{\dp0}
%\newdimen\Cwd
%\setlength\Cwd{3.25mm}
\newdimen\Cvs
\setlength\Cvs{\baselineskip}
%\setlength\Chs{\wd0}

\newcommand{\small}{%
 \@setfontsize\small\@viiipt{10.5\p@}%
 \abovedisplayskip 6\p@ \@plus2\p@ \@minus4\p@
 \abovedisplayshortskip \z@ \@plus\p@
 \belowdisplayshortskip 3\p@ \@plus\p@ \@minus2\p@
 \def\@listi{\leftmargin\leftmargini
             \topsep 3\p@ \@plus \p@ \@minus \p@
             \parsep 1\p@ \@plus \p@ \@minus \p@
             \itemsep \parsep}%
 \belowdisplayskip \abovedisplayskip}

\newcommand{\footnotesize}{%
 \@setfontsize\footnotesize\@viipt{9.5\p@}%
 \abovedisplayskip 5\p@ \@plus 1.5\p@ \@minus 3\p@
 \abovedisplayshortskip \z@ \@plus\p@
 \belowdisplayshortskip 2.5\p@ \@plus \p@ \@minus 1.5\p@
 \def\@listi{\leftmargin\leftmargini
             \topsep 2\p@ \@plus\p@ \@minus\p@
             \parsep 1\p@ \@plus\p@ \@minus\p@
             \itemsep \parsep}%
 \belowdisplayskip \abovedisplayskip}

\newcommand{\scriptsize}{\@setfontsize\scriptsize\@vipt\@viiipt}
\newcommand{\tiny}{\@setfontsize\tiny\@vpt\@vipt}
\newcommand{\large}{\@setfontsize\large\@xpt{12.5}}% abst+keyword
\newcommand{\Large}{\@setfontsize\Large\@xipt{\Cvs}}% sec
\newcommand{\LARGE}{\@setfontsize\LARGE\@xiipt{\Cvs}}% author
\newcommand{\huge}{\@setfontsize\huge\@xivpt{18}}% subtitle
\newcommand{\Huge}{\@setfontsize\Huge\@xviipt{25}}% ??

\headheight \z@
\headsep    \z@
\topskip    10\p@
\footskip   9.5mm
\maxdepth .5\topskip
\textwidth180mm
%\@settopoint\textwidth
\textheight63\Cvs
\advance \textheight \topskip
\advance \textheight .15mm
%\@settopoint\textheight

\if@twocolumn
  \setlength\marginparsep{5mm}
\else
  \setlength\marginparsep{5mm}
\fi
\setlength\marginparpush{5pt}

\topmargin\paperheight
\advance \topmargin -\textheight
\advance \topmargin -\headheight
\advance \topmargin -\headsep
\advance \topmargin -\footskip
\divide \topmargin \tw@
\advance \topmargin -1.25mm
\advance \topmargin -1in
%\@settopoint\topmargin
\oddsidemargin\paperwidth
\advance \oddsidemargin -\textwidth
\divide \oddsidemargin \tw@
\advance \oddsidemargin -1in
%\@settopoint\oddsidemargin
\evensidemargin\oddsidemargin
%\@settopoint\evensidemargin

\marginparwidth 20mm
%\@settopoint\marginparwidth

\setlength\footnotesep{6.65\p@}% 9.5 x .7
\setlength{\skip\footins}{1\Cvs plus .9\Cvs \@minus .3\Cvs}
\setlength\intextsep   {1.5\Cvs \@plus .75\Cvs \@minus .25\Cvs}
\setlength\floatsep    {1\Cvs \@plus .75\Cvs \@minus .25\Cvs}
\setlength\dblfloatsep {1\Cvs \@plus .75\Cvs \@minus .25\Cvs}
\setlength\textfloatsep{1.5\Cvs \@plus .75\Cvs \@minus .25\Cvs}
\setlength\dbltextfloatsep{1.5\Cvs \@plus .75\Cvs \@minus .25\Cvs}

\setlength\@fptop{0\p@ \@plus 1fil}
\setlength\@fpsep{8\p@ \@plus 2fil}
\setlength\@fpbot{0\p@ \@plus 1fil}
\setlength\@dblfptop{0\p@ \@plus 1fil}
\setlength\@dblfpsep{8\p@ \@plus 2fil}
\setlength\@dblfpbot{0\p@ \@plus 1fil}
\setlength\partopsep{2\p@ \@plus 1\p@ \@minus 1\p@}

\def\@listi{\leftmargin\leftmargini
  \parsep  4\p@ \@plus2\p@ \@minus\p@
  \topsep  8\p@ \@plus2\p@ \@minus4\p@
  \itemsep 4\p@ \@plus2\p@ \@minus\p@}
\let\@listI\@listi
\@listi
\def\@listii{\leftmargin\leftmarginii
   \labelwidth\leftmarginii \advance\labelwidth-\labelsep
   \topsep\z@ \@plus\p@ \@minus\p@
   \parsep\z@ \@plus\p@ \@minus\p@
   \itemsep\parsep}
\def\@listiii{\leftmargin\leftmarginiii
   \labelwidth\leftmarginiii \advance\labelwidth-\labelsep
   \topsep\z@ \@plus\p@ \@minus\p@
   \parsep\z@
   \partopsep\z@ \@plus\z@ \@minus\p@
   \itemsep\topsep}
\def\@listiv {\leftmargin\leftmarginiv
              \labelwidth\leftmarginiv
              \advance\labelwidth-\labelsep}
\def\@listv  {\leftmargin\leftmarginv
              \labelwidth\leftmarginv
              \advance\labelwidth-\labelsep}
\def\@listvi {\leftmargin\leftmarginvi
              \labelwidth\leftmarginvi
              \advance\labelwidth-\labelsep}

\columnsep3em
\columnseprule 0\p@
\lineskip 2\p@ 
\normallineskip 2\p@
\renewcommand{\baselinestretch}{}
\parskip\z@
\parindent1pc

\@lowpenalty   51
\@medpenalty  151
\@highpenalty 301
\setcounter{topnumber}{6}
\setcounter{bottomnumber}{5}
\setcounter{totalnumber}{11}
\setcounter{dbltopnumber}{5}
\renewcommand{\topfraction}{.95}
\renewcommand{\bottomfraction}{.95}
\renewcommand{\textfraction}{.05}
\renewcommand{\floatpagefraction}{.05}
\renewcommand{\dbltopfraction}{.95}
\renewcommand{\dblfloatpagefraction}{.05}

\if@Proof
 \def\@Rtop{\rlap{\smash{\rule[-\headsep]{0.05mm}{10mm}%
  \rule[-\headsep]{10mm}{0.05mm}}}}
 \def\@Ltop{\llap{\smash{\rule[-\headsep]{10mm}{0.05mm}%
  \rule[-\headsep]{0.05mm}{10mm}}}}
 \def\@Rbot{\rlap{\smash{\raisebox{1\footskip}
  {\rule[-10mm]{0.05mm}{10mm}\rule{10mm}{0.05mm}}}}}
 \def\@Lbot{\llap{\smash{\raisebox{1\footskip}
  {\rule{10mm}{0.05mm}\rule[-10mm]{0.05mm}{10mm}}}}}
\else
 \let\@Rtop\relax\let\@Ltop\relax\let\@Rbot\relax\let\@Lbot\relax
\fi

\def\ps@empty{%
 \def\@oddhead{\@Ltop\hfil\@Rtop}%
 \let\@evenhead\@oddhead
 \def\@oddfoot{\@Lbot\hfil\@Rbot}%
 \let\@evenfoot\@oddfoot
 \let\@mkboth\@gobbletwo
}

\def\tecrepyear#1{\gdef\tecrep@ft@year{#1}}
\def\tecrep@ft@year{20xx}%

\def\ps@FPtecrep{\let\@mkboth\@gobbletwo
  \def\@oddhead{\@Ltop\hfil\@Rtop}%
  \def\@oddfoot{\@Lbot{\normalsize
   This article is a technical report without peer review, 
   and its polished and/or extended version may be published elsewhere.}\hfil
   \smash{\lower3.5mm\llap{\normalsize
    Copyright \textcopyright\tecrep@ft@year\ by IEICE\hskip9pt}}%
   \@Rbot}%
  \let\@evenhead\@oddhead
  \let\@evenfoot\@oddfoot}

\def\ps@plain{\let\@mkboth\@gobbletwo
  \def\@oddhead{\@Ltop\hfil\@Rtop}%
  \def\@oddfoot{\@Lbot\reset@font\hfil ---\ \thepage\ ---\@Rbot}% \hfil
  \let\@evenhead\@oddhead
  \let\@evenfoot\@oddfoot}

\def\title#1{\gdef\@title{#1}}
\def\@title{}

\def\subtitle#1{\gdef\@subtitle{#1}}
\def\@subtitle{}

\def\@fnsymbol#1{\ifcase#1 \or % \ensuremath{
 \dagger\or
 {\dagger}{\dagger}\or
 {\dagger}{\dagger}{\dagger}\or
 {\dagger}{\dagger}{\dagger}{\dagger}\or
 {\dagger}{\dagger}{\dagger}{\dagger}{\dagger}\or
 {\dagger}{\dagger}{\dagger}{\dagger}{\dagger}{\dagger}\or
 {\dagger}{\dagger}{\dagger}{\dagger}{\dagger}{\dagger}{\dagger}\or
 {\dagger}{\dagger}{\dagger}{\dagger}{\dagger}{\dagger}{\dagger}{\dagger}\or
 {\dagger}{\dagger}{\dagger}{\dagger}{\dagger}{\dagger}%
  {\dagger}{\dagger}{\dagger}\or
 *\or {*}{*}\or {*}{*}{*}\or {*}{*}{*}{*}\or 
  {*}{*}{*}{*}{*}\or {*}{*}{*}{*}{*}{*}\or %% ((((((((((((((((((((
 a)\or b)\or c)\or d)\or e)\or f)\or g)\or h)\or i)\or j)\or
 k)\or l)\or m)\or n)\or o)\or p)\or q)\or r)\or s)\or t)\else
  \@ctrerr\fi}% }
%% mathTimePlus redefines \@fnsymbol. 
\let\tecrep@fnsymbol\@fnsymbol

\newtoks\@authorlist
\newcount\@authorcnt
\newcount\@alcnt
\newcount\p@alcnt
 \p@alcnt=9\relax
\newcount\@totalnumber

\def\authorlist#1{%
 \@authorlist={#1}\the\@authorlist
}

\def\authorentry{\@ifnextchar[% ]
 {\TR@ae}{\N@ae}}

\def\N@ae#1#2{\@ifnextchar[% ]
 {\@aeP{#1}{#2}}%
 {\@ae{#1}{#2}}}

\def\TR@ae[#1]#2#3{\@ifnextchar[% ]
 {\TR@aeP[#1]{#2}{#3}}%
 {\TR@aeNP[#1]{#2}{#3}}}

\def\fmt@Ean#1{%
 \@temptokena{#1}%
 \setbox\@tempboxa\hbox{\spaceskip=100mm #1}%
 \ifdim \wd\@tempboxa < 100mm
  \tecrep@warning{a space should be added between 1st and 2nd name: "#1"}%
 \else
  \def\name@form##1 ##2\@nil{\gdef\@tempan{##1 \uppercase{##2}}}%
  \expandafter\name@form\the\@temptokena\@nil
  \expandafter\@temptokena\expandafter{\@tempan}%
 \fi
 \def\@authorname{\the\@temptokena}%
}

\newif\if@affinone \@affinonefalse
\def\get@al#1{%
 \def\@noaffi{none}\def\@tempaffi{#1}%
 \ifx\@noaffi\@tempaffi
  \global\@affinonetrue
 \else
  \@for\get@label:=#1\do{%
   \@ifundefined{al@\get@label}%
    {%
     \global\advance \@alcnt \@ne
     \expandafter\xdef\csname al@\get@label\endcsname{\the\@alcnt}%
     \global\advance \@tempcnta \@ne
     \protected@xdef\plural@affi{\plural@affi
      \ifnum\@tempcnta=\@ne
       $^{\tecrep@fnsymbol{\csname al@\get@label\endcsname}}$%
      \else
       $^{,\tecrep@fnsymbol{\csname al@\get@label\endcsname}}$%
      \fi
     }%
    }%
    {%
     \global\advance \@tempcnta \@ne
     \protected@xdef\plural@affi{\plural@affi
      \ifnum\@tempcnta=\@ne
       $^{\tecrep@fnsymbol{\csname al@\get@label\endcsname}}$%
      \else
       $^{,\tecrep@fnsymbol{\csname al@\get@label\endcsname}}$%
      \fi
     }%
    }%
  }%
 \fi
}
\def\plural@affi{}

\def\get@p@al#1{%
 \@for\get@label:=#1\do{%
  \@ifundefined{p@al@\get@label}%
   {%
    \global\advance \p@alcnt \@ne
    \expandafter\xdef\csname p@al@\get@label\endcsname{\the\p@alcnt}%
    \global\advance \@tempcnta \@ne
    \protected@xdef\plural@p@affi{\plural@p@affi
     \ifnum\@tempcnta=\@ne
      $^{\tecrep@fnsymbol{\csname p@al@\get@label\endcsname}}$%
     \else
      $^{,\tecrep@fnsymbol{\csname p@al@\get@label\endcsname}}$%
     \fi
    }%
   }%
   {%
    \global\advance \@tempcnta \@ne
    \protected@xdef\plural@p@affi{\plural@p@affi
     \ifnum\@tempcnta=\@ne
      $^{\tecrep@fnsymbol{\csname p@al@\get@label\endcsname}}$%
     \else
      $^{,\tecrep@fnsymbol{\csname p@al@\get@label\endcsname}}$%
     \fi
    }%
   }%
 }%
}
\def\plural@p@affi{}

\def\@ae#1#2{%
 \@tempcnta\z@
 \advance \@authorcnt \@ne
 \get@al{#2}%
 \def\al@none{0}%
 \fmt@Ean{#1}%
 \expandafter\protected@xdef\csname @Eauthorname\number\@authorcnt\endcsname{%
  \@authorname\nobreak\plural@affi}% 
 \global\@totalnumber=\@authorcnt
 \def\plural@affi{}%
}

\def\@aeP#1#2[#3]{%
 \@tempcnta\z@
 \advance \@authorcnt \@ne
 \get@al{#2}%
 \def\al@none{0}%
 \@tempcnta\z@
 \get@p@al{#3}%
 \fmt@Ean{#1}%
 \expandafter\protected@xdef\csname @Eauthorname\number\@authorcnt\endcsname{%
  \@authorname\nobreak\plural@affi\nobreak\plural@p@affi
 }%
 \global\@totalnumber=\@authorcnt
 \def\plural@affi{}%
 \def\plural@p@affi{}%
}

\def\TR@aeNP[#1]#2#3{%
 \@tempcnta\z@
 \advance \@authorcnt \@ne
 \GetEma{#1}%
 \get@al{#3}%
 \def\al@none{0}%
 \fmt@Ean{#2}%
 \expandafter\protected@xdef\csname @Eauthorname\number\@authorcnt\endcsname{%
  \@authorname\nobreak\plural@affi %\nobreak\email@affi
 }% 
 \global\@totalnumber=\@authorcnt
 \def\plural@affi{}%
}

\def\TR@aeP[#1]#2#3[#4]{%
 \@tempcnta\z@
 \advance \@authorcnt \@ne
 \GetEma{#1}%
 \get@al{#3}%
 \def\al@none{0}%
 \@tempcnta\z@
 \get@p@al{#4}%
 \fmt@Ean{#2}%
 \expandafter\protected@xdef\csname @Eauthorname\number\@authorcnt\endcsname{%
  \@authorname\nobreak\plural@affi\nobreak\plural@p@affi %\nobreak\email@affi
 }%
 \global\@totalnumber=\@authorcnt
 \def\plural@affi{}%
 \def\plural@p@affi{}%
}

\bgroup
 \catcode`@=12\relax
 \gdef\GetEma#1{%
  \def\tempema{#1}%
  \ifx\tempema\empty
   \def\tempAnDn{n n.n.n}%
  \else
   \def\tempa##1@##2\nil{##1 ##2}% 
   \edef\tempAnDn{\expandafter\tempa\tempema\nil}%
  \fi
  \ProcessEma
 }%
\egroup

\newcount\tn@dn

\def\ProcessEma{%
 \def\tempa##1 ##2\@nil{%
  \@ifundefined{##2}
   {\expandafter\gdef\csname ##2\endcsname{##1}%
    \advance\tn@dn\@ne
    \expandafter\def\csname adrs\number\tn@dn\endcsname{##2}%
   }%
   {\expandafter\protected@xdef
    \csname ##2\endcsname{\csname ##2\endcsname,##1}%
   }%
 }% 
 \def\get@AnDn{\expandafter\tempa\tempAnDn\@nil}\get@AnDn
}

\def\fmt@Ema{%
 \@tempcntb\z@
 \loop
  \ifnum\@tempcntb<\tn@dn
   \advance\@tempcntb\@ne
   \def\ad@none{n.n.n}%
   \expandafter\ifx\csname adrs\number\@tempcntb\endcsname \ad@none
   \else
    \protected@edef\tmp@An{%
     \expandafter\csname \csname adrs\number\@tempcntb\endcsname \endcsname}%
    \@tempcnta\z@
    \@for\get@An:=\tmp@An\do{%
     \global\advance \@tempcnta \@ne
    }%
    \protected@xdef\Mail@ddress{%
     \ifx\Mail@ddress\empty\else\Mail@ddress,\ \fi
      \ifnum\@totalnumber=\@ne
       \if@affinone\else
        $\tecrep@fnsymbol{\the\@tempcntb}$%
       \fi
      \else
       $\tecrep@fnsymbol{\the\@tempcntb}$%
      \fi
      \ifnum\@tempcnta=\@ne
	\expandafter\csname \csname adrs\number\@tempcntb\endcsname \endcsname
	 @\csname adrs\number\@tempcntb\endcsname
      \else
	\{%% \protect
	 \expandafter\csname \csname adrs\number\@tempcntb\endcsname \endcsname
	  \}%
	 @\csname adrs\number\@tempcntb\endcsname
      \fi
    }%
    \gdef\header@ma{E-mail:}%
   \fi
 \repeat
}
\def\Mail@ddress{}
\def\header@ma{}

\def\MailAddress#1{\gdef\@MailAddress{#1}}
\def\@MailAddress{}

\def\breakauthorline#1{%
 \@for\@breakauthor:=#1\do{%
  \expandafter\gdef\csname @breakauthorline\@breakauthor\endcsname{\\}
 }%
  \@authorcnt\z@
  \loop\ifnum \@authorcnt < \@totalnumber
   \advance \@authorcnt \@ne
    \@ifundefined{@breakauthorline\number\@authorcnt}%
    {\expandafter\gdef\csname @breakauthorline\number\@authorcnt\endcsname
     {\relax}}{\relax}%
  \repeat
}

\newcount\totalnumberm@ne

\def\@outputEauthorlist{%
 \@authorcnt\z@
 \totalnumberm@ne\@totalnumber \advance \totalnumberm@ne -\@ne
  \loop\ifnum \@authorcnt < \@totalnumber
   \advance \@authorcnt \@ne 
    \ifnum \@authorcnt < \totalnumberm@ne
     \csname @Eauthorname\number\@authorcnt\endcsname\nobreak , 
      \csname @breakauthorline\number\@authorcnt\endcsname
    \else
     \ifnum \@authorcnt = \@totalnumber
      \csname @Eauthorname\number\@authorcnt\endcsname
     \else
      \csname @Eauthorname\number\@authorcnt\endcsname\nobreak
       \ifnum \@totalnumber=\tw@\ \else , \fi
        \csname @breakauthorline\number\@authorcnt\endcsname
      and\ \nobreak 
     \fi
    \fi
  \repeat
}

\newcount\chk@alcnt
\newcount\chk@p@alcnt

\def\affiliate[#1]#2{%
 \advance \chk@alcnt \@ne
 \@ifundefined{al@#1}%
  {\expandafter\def\csname al@#1\endcsname{1}%
   \tecrep@warning{Check the "#1" label, it does not correspond to
     ^^J\space\space any labels in \string\authorentry\space command}%
  }{}%
 \protected@xdef\E@affiliate{\E@affiliate
  $\protect\tecrep@fnsymbol{\csname al@#1\endcsname}$\ #2\\}%
}
\def\E@affiliate{}

\def\paffiliate[#1]#2{%
 \advance \chk@p@alcnt \@ne
 \@ifundefined{p@al@#1}%
  {\expandafter\def\csname p@al@#1\endcsname{1}%
   \tecrep@warning{Check the "#1" label, it does not correspond to
    ^^J\space\space any labels in \string\authorentry\space command}
  }{}%
 \protected@xdef\Ep@affiliate{\Ep@affiliate
  $\protect\tecrep@fnsymbol{\csname p@al@#1\endcsname}$\ #2}%
}
\def\Ep@affiliate{}

\newbox\abstractbox
\newbox\keywordbox
\def\abstract{\global\setbox\abstractbox=\hbox\bgroup
 \large{\bfseries Abstract}\hskip1em\ignorespaces}
\def\endabstract{\egroup}

\def\keyword{\global\setbox\keywordbox=\hbox\bgroup
 \large{\bfseries Key words}\hskip1em\ignorespaces}
\def\endkeyword{\egroup}

\def\titlepagebaselinestretch#1{\gdef\@titlepagebaselinestretch{#1}}
\titlepagebaselinestretch{1}

\def\maketitle{\par
 \begingroup 
 \ifnum \chk@alcnt < \@alcnt
   \tecrep@warning{information of \string\affiliate\space is not assigned}%
  \fi
  \advance \p@alcnt -9\relax
  \ifnum \chk@p@alcnt < \p@alcnt
   \tecrep@warning{information of \string\paffiliate\space is not assigned}%
  \fi
  \def\@fnsymbol##1{\ifcase##1 \or
   \dag\or
   \dag\dag\or
   \dag\dag\dag\or
   \dag\dag\dag\dag\or
   \dag\dag\dag\dag\dag\or
   \dag\dag\dag\dag\dag\dag\or
   \dag\dag\dag\dag\dag\dag\dag\or
   \dag\dag\dag\dag\dag\dag\dag\dag\or
   \dag\dag\dag\dag\dag\dag\dag\dag\dag\or
   *\or **\or ***\or ****\or *****\or ******\else\@ctrerr\fi\relax}%
  \def\thefootnote{\fnsymbol{footnote}}%
  \if@twocolumn
   \twocolumn[\@maketitle]%
  \else
   %\tecrep@warning{I don't recommend onecolumn option,
   % ^^J\space\space because of no compatibility with technicalreport option}%
   \@maketitle
  \fi
  \thispagestyle{FPtecrep}%
 \endgroup
  \let\maketitle\relax
  \let\@maketitle\relax
  \gdef\@affiliate{}
  \gdef\p@affiliate{}
  \gdef\@title{}
  \gdef\@subtitle{}
  \let\affiliate\relax
  \let\paffiliate\relax
  \@authorlist={}%
  \let\keyword\relax
  \let\abstract\relax
  \let\@outputEauthorlist\relax
  \let\TR@ae\relax
  \let\TR@aeP\relax
  \let\TR@aeNP\relax
  \let\breakauthorline\relax
  \@authorcnt \z@
  \loop\ifnum \the\@authorcnt < \the\@totalnumber
   \advance \@authorcnt \@ne
    \expandafter\let\csname @Jauthorname\number\@authorcnt\endcsname\relax
    \expandafter\let\csname @Eauthorname\number\@authorcnt\endcsname\relax
  \repeat
}

\def\@maketitle{%
 \setbox\@tempboxa\vbox{%
   \def\baselinestretch{\@titlepagebaselinestretch}%
   \hskip8mm
   \vtop{\footnotesize\baselineskip3mm
    \hbox{}% Shadan Houjin Denshi Jouhou Tsuushin Gakkai
    \hbox{}% THE INSTITUTE OF ELECTRONICS,
    \hbox{}% INFORMATION AND COMMUNICATION ENGINEERS
   }\hfill
   \vtop{\footnotesize\baselineskip3mm
    \hbox{}% ShingakuGihou
    \hbox{}% IEICE Technical Report
    \hbox{}%
   }\hskip8mm\hbox{}\par
   %\vskip\Cvs % v1.0N
   \bgroup
    \centering
    {\fontsize{18}{22}\selectfont
     \@title\par
    }%
    \vskip.75\Cvs
    \ifx\@subtitle\empty
    \else
     {\huge
      \@subtitle\par
     }%
     \vskip.25\Cvs
    \fi
    \vskip\Cvs
    {\LARGE
     \hyphenpenalty=10000\relax
     \@outputEauthorlist\par
    }%
    \vskip1\Cvs
    {\Large\baselineskip16\p@
     \E@affiliate\par
     \Ep@affiliate\par
     \vskip1\Cvs
     \ifx\@MailAddress\empty
      \fmt@Ema
      \ifx\header@ma\empty
       \vskip.5\Cvs
      \else
	E-mail: \Mail@ddress\par
	\vskip.5\Cvs
      \fi
     \else
      E-mail: \@MailAddress
     \fi
    }%
   \egroup
   \vskip1\Cvs
   \bgroup\large
    \leavevmode \unhbox\abstractbox\par
    \vskip\Cvs
    \leavevmode \unhbox\keywordbox
   \egroup
   \vskip\Cvs
 }%
 \@tempdima\ht\@tempboxa
 \advance \@tempdima \dp\@tempboxa
 \ifdim \@tempdima>\textheight
  \tecrep@warning{The title page is too high. 
     ^^J\space\space You can adjust the height of a title page
     ^^J\space\space by changing \string\titlepagebaselinestretch\space 
		      in preamble.
     ^^J\space\space For example, \string\titlepagebaselinestretch{0.9}}%
  {\parindent\z@
   \vtop to \z@{%
    \vbox to \textheight{%
     \unvbox\@tempboxa
    }\vss
   }%
  }\par
  \clearpage
 \else
  \divide \@tempdima \Cvs
  \@tempcnta=\@tempdima
  \advance \@tempcnta \@ne
  \vbox to \@tempcnta\Cvs{%
   \box\@tempboxa\vss
  }%
 \fi
}

\setcounter{secnumdepth}{5}
\newcounter{section}
\newcounter{subsection}[section]
\newcounter{subsubsection}[subsection]
\newcounter{paragraph}[subsubsection]
\newcounter{subparagraph}[paragraph]
\renewcommand{\thesection}{\@arabic\c@section}
\renewcommand{\thesubsection}{\thesection.\@arabic\c@subsection}
\renewcommand{\thesubsubsection}{\thesubsection.\@arabic\c@subsubsection}
\renewcommand{\theparagraph}{% (
 \@alph\c@paragraph\protect\,)}
\renewcommand{\thesubparagraph}{% (
 \@roman\c@subparagraph\protect\,)}

\def\@afterheading{%
 \global\@nobreaktrue
 \everypar{%
  \if@nobreak
   \global\@nobreakfalse
   \clubpenalty \z@
    \if@afterindent
    \else
     {\setbox\z@=\lastbox}%
    \fi
  \else
   \clubpenalty\@clubpenalty
   \everypar{}%
  \fi}%
}

%% \@startsection{NAME}{LEVEL}{INDENT}{BEFORESKIP}{AFTERSKIP}{STYLE}
\def\@startsection#1#2#3#4#5#6{\if@noskipsec \leavevmode \fi
  \par \@tempskipa #4\relax
  \@afterindenttrue
  \ifdim \@tempskipa <\z@ \@tempskipa -\@tempskipa \@afterindentfalse\fi
  \if@nobreak
   \everypar{}%
  \else
   %\addpenalty\@secpenalty
   %%
   \ifdim\@tempskipa>\z@
    \ifnum#2=\@ne
     \vskip-\prevdepth \prevdepth\z@ \vskip\Cvs
     \advance\@tempskipa-2\Cvs
     \vspace{\Cvs}
     \vspace*{\@tempskipa}
    \else
     \vskip-\prevdepth \prevdepth\z@ \vskip\Cvs
     \advance\@tempskipa-\Cvs
     \vspace*{\@tempskipa}
    \fi
   \fi
  \fi
 \@ifstar{\@ssect{#3}{#4}{#5}{#6}}{\@dblarg{\@sect{#1}{#2}{#3}{#4}{#5}{#6}}}}

%% \@sect{NAME}{LEVEL}{INDENT}{BEFORESKIP}{AFTERSKIP}{STYLE}[ARG1]{ARG2}
\def\@sect#1#2#3#4#5#6[#7]#8{%%
 \ifnum #2>\c@secnumdepth
  \let\@svsec\@empty
 \else
  \refstepcounter{#1}%
  \protected@edef\@svsec{\@seccntformat{#1}\relax}%
 \fi
  \@tempskipa #5\relax
  \ifdim \@tempskipa<\z@
   \def\@svsechd{%
     #6{\hskip #3\relax
     \@svsec #8}}%
  \else
   \begingroup
    #6{%
      \@hangfrom{\hskip #3\relax{\csname #2@font\endcsname \@svsec}}%
       \interlinepenalty\@M #8\@@par
      }%
   \endgroup
  \fi
 \@xsect{#5}}

%% \@ssect{INDENT}{BEFORESKIP}{AFTERSKIP}{STYLE}{ARG} ==
\def\@ssect#1#2#3#4#5{%
 \@tempskipa #3\relax
 \ifdim \@tempskipa<\z@
  \def\@svsechd{#4{\hskip #1\relax #5}}%
 \else
  \begingroup
   #4{%
    \@hangfrom{\hskip #1}%
     \interlinepenalty\@M #5\@@par
     }%
  \endgroup
 \fi
 \@xsect{#3}}

\def\@xsect#1{%
  \@tempskipa #1\relax
  \ifdim \@tempskipa<\z@
    \@nobreakfalse
    \global\@noskipsectrue
    \everypar{%
      \if@noskipsec
        \global\@noskipsecfalse
       {\setbox\z@\lastbox}%
        \clubpenalty\@M
        \begingroup \@svsechd \endgroup
        \unskip
        \@tempskipa #1\relax
        \hskip -\@tempskipa
        \pagebreak[2]%
      \else
        \clubpenalty \@clubpenalty
        \everypar{}%
      \fi}%
  \else
    \par \nobreak
    \vskip \@tempskipa
    \@afterheading
  \fi
  \ignorespaces}

\@namedef{3@font}{\bfseries}
\def\@seccntformat#1{\csname the#1\endcsname
 \csname dotafter@#1\endcsname\hskip1em}
\def\dotafter@section{.}

\def\sec@font{\Large\bfseries\mathversion{bold}\baselineskip\Cvs}

\newcommand{\section}{\@startsection{section}{1}{1pc}%
  {1.5\Cvs}% \@plus.1mm \@minus.1mm
  {.5\Cvs}% \@plus.1mm \@minus.1mm
  {\reset@font\sec@font}}
\newcommand{\subsection}{\@startsection{subsection}{2}{1pc}%
  {\z@}% \@plus.1mm \@minus.1mm
  {\z@}% \@plus.1mm \@minus.1mm
  {\reset@font\normalsize\bfseries\mathversion{bold}}}
\newcommand{\subsubsection}{\@startsection{subsubsection}{3}{1pc}%
  {\z@}% \@plus.1mm \@minus.1mm
  {\z@}% \@plus.1mm \@minus.1mmu
  {\reset@font\normalsize}}
\newcommand{\paragraph}{\@startsection{paragraph}{4}{1pc}%
   {\z@}% \@plus.1mm \@minus.1mm
   {\z@}% \@plus.1mm \@minus.1mm
   {\reset@font\normalsize}}
\newcommand{\subparagraph}{\@startsection{subparagraph}{5}{1pc}%
   {\z@}% \@plus.1mm \@minus.1mm
   {\z@}% \@plus.1mm \@minus.1mm
   {\reset@font\normalsize}}

\newcommand{\appendix}{\par
 \renewcommand{\section}{\@startsection{section}{1}{\z@}
  {1.5\Cvs}% \@plus.1mm \@minus.1mm
  {.5\Cvs}% \@plus.1mm \@minus.1mm
  {\centering\sec@font}}%
 \section*{Appendix}
  \renewcommand{\section}{\@startsection{section}{1}{1pc}
   {\z@}% \@plus.1mm \@minus.1mm
   {\z@}% \@plus.1mm \@minus.1mm
   {\normalsize\bfseries\mathversion{bold}}}%
 \setcounter{section}{0}%
 \setcounter{subsection}{0}%
 \setcounter{equation}{0}%
 \setcounter{figure}{0}%
 \setcounter{table}{0}%
 \def\theequation{\protect\mbox{A$\cdot$\@arabic\c@equation}}%
 \def\thefigure{A$\cdot$\@arabic\c@figure}%
 \def\thetable{A$\cdot$\@arabic\c@table}%
}

\if@twocolumn
  \setlength\leftmargini {2em}%
\else
  \setlength\leftmargini {2em}%
\fi
\setlength\leftmarginii  {2em}%
\setlength\leftmarginiii {2em}%
\setlength\leftmarginiv  {2em}%
\if@twocolumn
  \setlength\leftmarginv {1em}%
  \setlength\leftmarginvi{1em}%
\else
  \setlength\leftmarginv {1em}%
  \setlength\leftmarginvi{1em}%
\fi
\setlength  \labelsep  {1em}%
\setlength  \labelwidth{\leftmargini}
\addtolength\labelwidth{-\labelsep}
\@beginparpenalty \z@ % -\@lowpenalty
\@endparpenalty   \z@ % -\@lowpenalty
\@itempenalty     \z@ % -\@lowpenalty

%% from latex.ltx
\def\@item[#1]{%
  \if@noparitem
    \@donoparitem
  \else
    \if@inlabel
      \indent \par
    \fi
    \ifhmode
      \unskip\unskip \par
    \fi
    \if@newlist
      \if@nobreak
        \@nbitem
      \else
        \addpenalty\@beginparpenalty
        \addvspace\@topsep
        \addvspace{-\parskip}%
      \fi
    \else
      \addpenalty\@itempenalty
      \addvspace\itemsep
    \fi
    \global\@inlabeltrue
  \fi
  \everypar{%
    \@minipagefalse
    \global\@newlistfalse
    \if@inlabel
      \global\@inlabelfalse
      {\setbox\z@\lastbox
       \ifvoid\z@
         \kern-\itemindent
       \fi}%
      \box\@labels
      \penalty\z@
    \fi
    \if@nobreak
      \@nobreakfalse
      \clubpenalty\z@ % \@M --> \z@
    \else
      \clubpenalty \@clubpenalty
      \everypar{}%
    \fi}%
  \if@noitemarg
    \@noitemargfalse
    \if@nmbrlist
      \refstepcounter\@listctr
    \fi
  \fi
  \sbox\@tempboxa{\makelabel{#1}}%
  \global\setbox\@labels\hbox{%
    \unhbox\@labels
    \hskip \itemindent
    \hskip -\labelwidth
    \hskip -\labelsep
    \ifdim \wd\@tempboxa >\labelwidth
      \box\@tempboxa
    \else
      \hbox to\labelwidth {\unhbox\@tempboxa}%
    \fi
    \hskip \labelsep}%
}

\renewcommand{\theenumi}{\@arabic\c@enumi}
\renewcommand{\theenumii}{\@alph\c@enumii}
\renewcommand{\theenumiii}{\@roman\c@enumiii}
\renewcommand{\theenumiv}{\@Alph\c@enumiv}
\newcommand{\labelenumi}{(\theenumi)}
\newcommand{\labelenumii}{(\theenumii)}
\newcommand{\labelenumiii}{\theenumiii.}
\newcommand{\labelenumiv}{\theenumiv.}
\renewcommand{\p@enumii}{\theenumi}
\renewcommand{\p@enumiii}{\theenumi(\theenumii)}
\renewcommand{\p@enumiv}{\p@enumiii\theenumiii}

\renewenvironment{enumerate}
  {\ifnum \@enumdepth >3\relax\@toodeep\else
   \advance\@enumdepth\@ne
   \edef\@enumctr{enum\romannumeral\the\@enumdepth}%
   \list{\csname label\@enumctr\endcsname}{%
         \topsep.5\Cvs\parsep\z@\partopsep\z@\itemsep\z@
         \settowidth{\labelwidth}{\csname label\@enumctr\endcsname}%
         \labelsep.5em
         \leftmargin\labelwidth
         \advance\leftmargin \labelsep
         %\advance\leftmargin 1em
         \listparindent1pc
         \clubpenalty\z@
         \widowpenalty\z@
         \@itempenalty\z@
         \usecounter{\@enumctr}%
         \def\makelabel##1{\hss\llap{##1}}}%
   \fi}{\endlist}

\newcommand{\labelitemi}{\leavevmode\hbox to 1em{\hss \textbullet\hss}}
\newcommand{\labelitemii}{{\normalfont\bfseries\textendash}}
\newcommand{\labelitemiii}{\textasteriskcentered}
\newcommand{\labelitemiv}{\textperiodcentered}

\def\itemize{%
  \ifnum \@itemdepth >\thr@@\@toodeep\else
    \advance\@itemdepth\@ne
    \edef\@itemitem{labelitem\romannumeral\the\@itemdepth}%
    \expandafter
    \list
      \csname\@itemitem\endcsname
      {\ifnum\@itemdepth=\@ne
        \topsep.5\Cvs
       \else
        \topsep\z@
       \fi
       \labelsep.25em
       \listparindent1pc
       \parsep\z@\partopsep\z@\itemsep\z@
       \def\makelabel##1{\hss\llap{##1}}}%
  \fi}

\newenvironment{description}
 {\list{}{\topsep.5\Cvs\parsep\z@\partopsep\z@\itemsep\z@
          \labelwidth\z@ \itemindent-\leftmargin
          \let\makelabel\descriptionlabel}}
               {\endlist}
\newcommand*\descriptionlabel[1]{\hspace\labelsep
                                \normalfont\bfseries #1}

\newenvironment{verse}
  {\let\\\@centercr
   \list{}{\itemsep\z@
           \topsep.5\Cvs\parsep\z@\partopsep\z@\itemsep\z@
           \itemindent -1.5em
           \listparindent\itemindent
           \rightmargin\leftmargin
           \advance\leftmargin 1.5em}%
           \item\relax}{\endlist}

\newenvironment{quotation}
  {\list{}{\listparindent 1.5em
           \itemindent\listparindent
           \rightmargin\leftmargin
           \topsep.5\Cvs\parsep\z@\partopsep\z@\itemsep\z@
           }%
           \item\relax}{\endlist}

\newenvironment{quote}
  {\list{}{%
           \topsep.5\Cvs\parsep\z@\partopsep\z@\itemsep\z@
           \rightmargin\leftmargin}%
           \item\relax}{\endlist}

\gdef\tabbing{\lineskip \z@skip\let\>\@rtab\let\<\@ltab\let\=\@settab
     \let\+\@tabplus\let\-\@tabminus\let\`\@tabrj\let\'\@tablab
     \let\\=\@tabcr
     \@hightab\@firsttab
     \global\@nxttabmar\@firsttab
     \dimen\@firsttab\@totalleftmargin
     \global\@tabpush\z@ \global\@rjfieldfalse
     \topsep.5\Cvs\parsep\z@\partopsep\z@\itemsep\z@
     \trivlist \item\relax
     \if@minipage\else\vskip\parskip\fi
     \setbox\@tabfbox\hbox{%
       \rlap{\hskip\@totalleftmargin\indent\the\everypar}}%
     \def\@itemfudge{\box\@tabfbox}%
     \@startline\ignorespaces}

\newdimen\verbatimleftmargin
  \verbatimleftmargin\z@
\newdimen\verbatimbaselineskip
  \verbatimbaselineskip\Cvs
\def\verbatimsize{\normalsize}

\def\@verbatim{%
 \topsep\z@\partopsep\z@\parsep\z@\itemsep\z@
 \trivlist \item\relax
  \if@minipage\else
   \vskip\baselineskip
   \vskip-\verbatimbaselineskip
  \fi
  \leftskip\@totalleftmargin
  \if@minipage\else
   \advance \leftskip by \verbatimleftmargin
  \fi
  \rightskip\z@skip
  \parindent\z@\parfillskip\@flushglue\parskip\z@skip
  \@@par
  \@tempswafalse
  \def\par{%
    \if@tempswa
      \leavevmode \null \@@par\penalty\interlinepenalty
    \else
      \@tempswatrue
      \ifhmode\@@par\penalty\interlinepenalty\fi
    \fi}%
  \let\do\@makeother \dospecials
  \obeylines 
   \verbatimsize \baselineskip\verbatimbaselineskip
   \ttfamily \@noligs
  \everypar \expandafter{\the\everypar \unpenalty}%
}

\newcounter{figure}
\renewcommand{\thefigure}{\@arabic\c@figure}
\def\fps@figure{tbp}
\def\ftype@figure{1}
\def\ext@figure{lof}
\def\fnum@figure{\figurename\,\thefigure}
\newenvironment{figure}
               {\@floatenv
                \capwidth\hsize
                \abovecaptionskip.5mm\belowcaptionskip\z@\@float{figure}}
               {\end@float}
\newenvironment{figure*}
               {\@floatenv\capwidth.66\textwidth
                \abovecaptionskip.5mm\belowcaptionskip\z@\@dblfloat{figure}}
               {\end@dblfloat}
\newcounter{table}
\renewcommand{\thetable}{\@arabic\c@table}
\def\fps@table{tbp}
\def\ftype@table{2}
\def\ext@table{lot}
\def\fnum@table{\tablename~\thetable}
\newenvironment{table}
               {\@floatenv
                \capwidth\hsize
                \abovecaptionskip\z@\belowcaptionskip3pt\@float{table}}
               {\end@float}
\newenvironment{table*}
               {\@floatenv\capwidth.66\textwidth
                \abovecaptionskip\z@\belowcaptionskip3pt\@dblfloat{table}}
               {\end@dblfloat}

\def\@floatboxreset {%
 \reset@font
 \normalsize\tabcolsep.5em
 \@setminipage
}
\def\@floatenv{\let\center\Center}

\def\Center{\topsep\z@\parsep\z@\partopsep\z@\itemsep\z@
 \trivlist \centering\item\relax}
\def\endCenter{\endtrivlist}

\long\def\@caption#1[#2]#3{\par
 \begingroup
  \@parboxrestore
  \if@minipage
   \@setminipage
  \fi
  \normalsize
  \@makecaption{\csname fnum@#1\endcsname}{\ignorespaces #3}\par
 \endgroup}

\newlength\abovecaptionskip
\newlength\belowcaptionskip

\newbox\@tempboxb
\newdimen\capwidth

\long\def\@makecaption#1#2{%
 \vskip\abovecaptionskip
 \setbox\@tempboxa\hbox{#1\hskip1em\shortstack[l]{#2}}%
 \@tempdima\ht\@tempboxa \advance \@tempdima \dp\@tempboxa
 \setbox\@tempboxb\hbox{#1\hskip1em}%
 \ifdim \@tempdima > \baselineskip
  \ifdim \wd\@tempboxa > \capwidth
   \hfil\parbox[t]{\capwidth}{\hangindent\wd\@tempboxb 
    #1\hskip1em #2}\par
  \else
   \hfil\parbox[t]{\wd\@tempboxa}{\hangindent\wd\@tempboxb 
    #1\hskip1em #2}\par
  \fi
 \else
  \ifdim \wd\@tempboxa > \capwidth
   \hfil\parbox[t]{\capwidth}{\hangindent\wd\@tempboxb 
    #1\hskip1em #2}\par
  \else
   \hbox to\hsize{\hfil\box\@tempboxa\hfil}\par
  \fi
 \fi
 \vspace{\belowcaptionskip}\par
}

\setlength\arraycolsep{5\p@}
\setlength\tabcolsep{6\p@}
\setlength\arrayrulewidth{.1mm}
\setlength\doublerulesep{\z@}
\setlength\tabbingsep{\labelsep}

\skip\@mpfootins = \skip\footins
\setlength\fboxsep{3\p@}
\setlength\fboxrule{.1mm}
\renewcommand{\theequation}{\@arabic\c@equation}

\@ifundefined{mathmc}{}{%
 \if@enablejfam
  \if@compatibility\else
    \DeclareSymbolFont{mincho}{\kenc@JYn}{mc}{m}{n}
    \DeclareSymbolFontAlphabet{\mathmc}{mincho}
    \SetSymbolFont{mincho}{bold}{\kenc@JYn}{gt}{m}{n}
    \jfam\symmincho
    \DeclareMathAlphabet{\mathgt}{\kenc@JYn}{gt}{m}{n}
  \fi
  \if@mathrmmc
    \AtBeginDocument{%
     \reDeclareMathAlphabet{\mathrm}{\mathrm}{\mathmc}
     \reDeclareMathAlphabet{\mathbf}{\mathbf}{\mathgt}
    }%
  \fi
 \else
  \DeclareRobustCommand{\mathmc}{%
    \@latex@error{Command \noexpand\mathmc invalid with\space
       `disablejfam' class option.}\@eha
  }
  \DeclareRobustCommand{\mathgt}{%
    \@latex@error{Command \noexpand\mathgt invalid with\space
       `disablejfam' class option.}\@eha
  }
 \fi
}

\@ifundefined{mathmc}{\relax}{%
 \DeclareOldFontCommand{\mc}{\normalfont\mcfamily}{\mathmc}
 \DeclareOldFontCommand{\gt}{\normalfont\gtfamily}{\mathgt}
}

\DeclareOldFontCommand{\rm}{\normalfont\rmfamily}{\mathrm}
\DeclareOldFontCommand{\sf}{\normalfont\sffamily}{\mathsf}
\DeclareOldFontCommand{\tt}{\normalfont\ttfamily}{\mathtt}
\DeclareOldFontCommand{\bf}{\normalfont\bfseries}{\mathbf}
\DeclareOldFontCommand{\it}{\normalfont\itshape}{\mathit}
\DeclareOldFontCommand{\sl}{\normalfont\slshape}{\@nomath\sl}
\DeclareOldFontCommand{\sc}{\normalfont\scshape}{\@nomath\sc}
\DeclareRobustCommand*{\cal}{\@fontswitch\relax\mathcal}
\DeclareRobustCommand*{\mit}{\@fontswitch\relax\mathnormal}

\newdimen\bibindent
\setlength\bibindent{1.5em}
\newcommand{\newblock}{\hskip .11em\@plus.33em\@minus.07em}

\newenvironment{thebibliography}[1]
 {%
 \def\subsection{\@startsection{subsection}{2}{\z@}%
  {\z@}%     \@plus 1mm \@minus .1mm
  {.15\Cvs}% \@plus 1mm \@minus .1mm
  {\centering\bfseries}}%
 \subsection*{\refname}%
 \small %\baselineskip11\p@
   \list{\@biblabel{\@arabic\c@enumiv}}%
        {\settowidth\labelwidth{\@biblabel{#1}}%
         \topsep\z@\parsep\z@\partopsep\z@\itemsep\z@
         \leftmargin\labelwidth
         \advance\leftmargin\labelsep
         %\leftmargin3em
         %\labelsep1em
         \@openbib@code
         \usecounter{enumiv}%
         \let\p@enumi\@empty
         \renewcommand\theenumiv{\@arabic\c@enumiv}}%
   \sloppy
   \clubpenalty\z@
   \widowpenalty\z@
   \@clubpenalty\clubpenalty
   \sfcode`\.\@m}
  {\def\@noitemerr
    {\@latex@warning{Empty `thebibliography' environment}}%
   \endlist}
\def\@biblabel#1{[#1]}
\let\@openbib@code\@empty

\renewcommand{\footnoterule}{%
  \kern-3\p@
  \hrule height .1mm width \columnwidth
  \kern 2.715\p@}

\let\org@footnote\footnote
\def\footnote{\unskip\penalty\@M\org@footnote}

%\def\@makefnmark{\hbox{$^{\mbox{\tiny 
%  (\@thefnmark)}}$}}

\newcommand\@makefntext[1]{\parindent1pc
 \noindent\hbox{%
  (\@thefnmark):\ }#1}

\def\thefootnote{\@arabic\c@footnote}
\def\thempfootnote{\@fnsymbol\c@mpfootnote}

\newdimen\mathindent
\AtEndOfClass{\mathindent1pc}% --> @mathmargin

\def\eqnarray{%
    \stepcounter{equation}%
    \def\@currentlabel{\p@equation\theequation}%
    \global\@eqnswtrue\m@th
    \global\@eqcnt\z@
    \tabskip\mathindent
    \let\\=\@eqncr
    \setlength\abovedisplayskip{\topsep}%
    \ifvmode
      \addtolength\abovedisplayskip{\partopsep}%
    \fi
    \addtolength\abovedisplayskip{\parskip}%
    \setlength\belowdisplayskip{\abovedisplayskip}%
    \setlength\belowdisplayshortskip{\abovedisplayskip}%
    \setlength\abovedisplayshortskip{\abovedisplayskip}%
    $$\everycr{}\halign to\linewidth% $$
    \bgroup
      \hskip\@centering$\displaystyle\tabskip\z@skip{##}$\@eqnsel
      &\global\@eqcnt\@ne \hfil$\displaystyle{{}##{}}$\hfil
      &\global\@eqcnt\tw@
        $\displaystyle{##}$\hfil \tabskip\@centering
      &\global\@eqcnt\thr@@ \hb@xt@\z@\bgroup\hss##\egroup
    \tabskip\z@skip\cr
    }

\def\@eqnnum{{\normalfont \normalcolor (\theequation)\hspace*{3mm}}}

\def\@begintheorem#1#2{%
 \settowidth{\labelwidth}{[#1\ #2]}
 \begin{description}
  \item[\@thmlbracket #1\ #2\@thmrbracket]}

\def\@opargbegintheorem#1#2#3{%
 \begin{description}
  \item[\@thmlbracket #1\ #2\@thmrbracket (#3)]}%%
\def\@endtheorem{\end{description}}

\def\thmbracket#1#2{\gdef\@thmlbracket{#1}\gdef\@thmrbracket{#2}}
\thmbracket{[}{]}
\def\@thmcountersep{}

\def\ack{\par{\bfseries Acknowledgements}\hskip1em}

%%\newcommand{\contentsname}{Contents}
%%\newcommand{\listfigurename}{List of Figures}
%%\newcommand{\listtablename}{List of Tables}
\newcommand{\refname}{References}
%%\newcommand{\indexname}{Index}
\newcommand{\figurename}{Fig.}
\newcommand{\tablename}{Table}
%%\newcommand{\appendixname}{Appendix}
%%\newcommand{\abstractname}{Abstract}

%% from "citesort.sty", a little customized
\newcount\@minsofar
\newcount\@min
\newcount\@cite@temp
\def\@citex[#1]#2{%
\if@filesw \immediate \write \@auxout {\string \citation {#2}}\fi
\@tempcntb\m@ne \let\@h@ld\relax \def\@citea{}%
\@min\m@ne%
\@cite{%
  \@for \@citeb:=#2\do {\@ifundefined {b@\@citeb}%
    {\@h@ld\@citea\@tempcntb\m@ne{\bfseries ?}%
    \@warning {Citation `\@citeb ' on page \thepage \space undefined}}%
{\@minsofar\z@ \@for \@scan@cites:=#2\do {%
  \@ifundefined{b@\@scan@cites}%
    {\@cite@temp\m@ne}
    {\@cite@temp\number\csname b@\@scan@cites \endcsname \relax}%
\ifnum\@cite@temp > \@min% select the next one to list
    \ifnum\@minsofar = \z@
      \@minsofar\number\@cite@temp
      \edef\@scan@copy{\@scan@cites}\else
    \ifnum\@cite@temp < \@minsofar
      \@minsofar\number\@cite@temp
      \edef\@scan@copy{\@scan@cites}\fi\fi\fi}\@tempcnta\@min
  \ifnum\@minsofar > \z@ % some more
    \advance\@tempcnta\@ne
    \@min\@minsofar
    \ifnum\@tempcnta=\@minsofar %   Number follows previous--hold on to it
      \ifx\@h@ld\relax
        \edef \@h@ld{\@citea\csname b@\@scan@copy\endcsname}%
      \else \edef\@h@ld{\ifmmode{]{-}[}\else]--[\fi
       \csname b@\@scan@copy\endcsname}%
      \fi
    \else \@h@ld\@citea\csname b@\@scan@copy\endcsname
          \let\@h@ld\relax
  \fi % no more
\fi}%
\def\@citea{],\penalty\@highpenalty\,[}}\@h@ld}{#1}}
%% end of citesort.sty

\def\@cite#1#2{\leavevmode\unskip
  \ifnum\lastpenalty=\z@\penalty\@highpenalty\fi% highpenalty before
  \,[{\multiply\@highpenalty 3 #1%             % triple-highpenalties within
      \if@tempswa,\penalty\@highpenalty\ #2\fi % and before note.
    }]\spacefactor\@m}

\def\onelineskip{\par\vspace{1\baselineskip}\par}
\def\halflineskip{\par\vspace{.5\baselineskip}\par}

\def\FRAC#1#2{\leavevmode\kern-.1em
  \raise.5ex\hbox{\the\scriptfont0 #1}\kern-.1em
  /\kern-.15em\lower.25ex\hbox{\the\scriptfont0 #2}}
\def\RN#1{\uppercase\expandafter{\romannumeral#1}}

\def\MARU#1{\raisebox{.4ex}{{%
 \leavevmode\ooalign{\hfil\lower.168ex\hbox{#1}\hfil\crcr\mathhexbox20D}}}}

\def\QED{{\unskip\nobreak\hfil\penalty50
 \hskip1em\hbox{}\nobreak\hfil \hbox{$\Box$\hskip1em}
 \parfillskip\z@ \finalhyphendemerits\z@\par}}

\def\Hline{\noalign{\hrule height 0.4mm}}

\def\leq{\mathrel{\mathpalette\gl@align<}} \let\le\leq
\def\geq{\mathrel{\mathpalette\gl@align>}} \let\ge\geq
\def\gl@align#1#2{\lower.6ex\vbox{\baselineskip\z@skip\lineskip\z@
 \ialign{$\m@th#1\hfil##\hfil$\crcr#2\crcr=\crcr}}}
\def\subseteq{\rlap{\raisebox{.25ex}{$\subset$}}\raisebox{-1.1ex}{$=$}}
\def\supseteq{\rlap{\raisebox{.25ex}{$\supset$}}\raisebox{-1.1ex}{$=$}}
\def\neq{\mathrel{\mathpalette\c@ncelass=}}
\def\c@ncelass#1#2{\ooalign{$\hfil#1\mkern-.4mu|\hfil$\crcr$#1#2$}}
\let\ne\neq

\@ifundefined{@needsPformat}{}{% kanjiskip
 \postbreakpenalty"5C=10000 %%"
}

\def\sloppy{\tolerance9999\hbadness9999\hfuzz.5\p@ \vfuzz.5\p@}

\hbadness4000
\vbadness10001
\tolerance4000\pretolerance\m@ne
\clubpenalty\z@
\widowpenalty\z@

\AtBeginDocument{%
 \@ifpackageloaded{newtxtext}{%
  \def\@makefnmark{\hbox{$^{\mbox{\tiny (\@thefnmark)}}$}}%
 }{}%
 \displaywidowpenalty\z@
 \interdisplaylinepenalty\z@
 \predisplaypenalty\z@
 \postdisplaypenalty\z@
 %% amsmath
 \@ifpackageloaded{amsmath}{%
   \@mathmargin1pc \@plus\z@ \@minus\z@
   \def\maketag@@@#1{\hbox{\m@th\normalfont #1}\hskip3mm}%
   \def\eqref#1{\textup{\tagform@{\ref{#1}}\unskip}}%
 }{}%
 %% enumerate
 \@ifpackageloaded{enumerate}{%
  \def\@@enum@[#1]{%
    \@enLab{}\let\@enThe\@enQmark
    \@enloop#1\@enum@
    \ifx\@enThe\@enQmark\@warning{The counter will not be printed.%
     ^^J\space\@spaces\@spaces\@spaces The label is: \the\@enLab}\fi
    \expandafter\edef\csname label\@enumctr\endcsname{\the\@enLab}%
    \expandafter\let\csname the\@enumctr\endcsname\@enThe
    \csname c@\@enumctr\endcsname7
    \expandafter\settowidth
              \csname leftmargin\romannumeral\@enumdepth\endcsname
              {\the\@enLab\hspace{.5em}}% <-- \labelsep
    \@enum@}%
  \def\@enum@{%
   \list{\csname label\@enumctr\endcsname}%
    {\labelsep.5em
     \expandafter\leftmargin\csname leftmargin\romannumeral\@enumdepth\endcsname
     \listparindent1pc
     \ifnum \@enumdepth=\@ne
      \topsep.5\Cvs
     \else
      \topsep\z@
     \fi
     \parsep\z@\partopsep\z@\itemsep\z@
     %%
     \usecounter{\@enumctr}\def\makelabel##1{\hss\llap{##1}}}%
  }%
 }{}%
 %% cite
 %% natbib
}

\pagestyle{plain}

\pagenumbering{arabic}
\raggedbottom
\if@twocolumn
 \twocolumn
 \sloppy
 \raggedbottom
\else
 \onecolumn
\fi
\if@twoside
  \@mparswitchtrue
\else
  \@mparswitchfalse
\fi

\endinput
