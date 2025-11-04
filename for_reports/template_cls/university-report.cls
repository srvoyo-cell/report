\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{university-report}[2025/11/02 University Report Class]

\LoadClass[14pt]{extarticle}

% ==================================================
% ПАКЕТЫ
% ==================================================
\RequirePackage{float, pdfpages, hyphenat, geometry, polyglossia, fontspec}
\RequirePackage{amsmath, amssymb, setspace, titlesec, fancyhdr, graphicx, array, tabularx, caption, xcolor, listings, tocloft, enumitem, csquotes}
\RequirePackage{xifthen} % для проверки пустых аргументов
\RequirePackage{pgfplots, tikz}
\RequirePackage{multirow}
\RequirePackage{makecell}
\RequirePackage{icomma}
\MakeOuterQuote{"}

% ==================================================
% ЯЗЫКИ
% ==================================================
\setmainlanguage{russian}
\setotherlanguage{english}

% ==================================================
% ШРИФТЫ
% ==================================================
\setmainfont{Times New Roman}
\newfontfamily\cyrillicfont{Times New Roman}
\setmonofont{Fira Code}[Scale=0.9]
\newfontfamily\cyrillicfonttt{Fira Code}[Scale=0.9,Script=Cyrillic]

% ==================================================
% ПОЛЯ
% ==================================================
\geometry{
  a4paper,
  top=2cm,
  bottom=2cm,
  left=3cm,
  right=1.5cm,
  headheight=0pt,
  headsep=0pt,
}

% ==================================================
% МЕЖСТРОЧНЫЙ И АБЗАЦНЫЙ ОТСТУП
% ==================================================
\onehalfspacing
\setlength{\parindent}{1.25cm}
\setlength{\topskip}{0pt}

% ==================================================
% КОЛОНТИТУЛЫ
% ==================================================
\pagestyle{fancy}
\fancyhf{}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}
\fancyfoot[C]{\fontsize{12pt}{12pt}\selectfont \thepage}

% ==================================================
% ЗАГОЛОВКИ РАЗДЕЛОВ
% ==================================================
\titleformat{\section}[block]{\fontsize{14pt}{16pt}\bfseries}{\thesection.}{1em}{}
\titlespacing*{\section}{\parindent}{0pt}{0pt}

\titleformat{\subsection}[hang]{\fontsize{14pt}{16pt}\bfseries}{\thesubsection.}{1em}{}
\titlespacing*{\subsection}{\parindent}{0pt}{0pt}

% ==================================================
% СТРУКТУРНЫЕ ЭЛЕМЕНТЫ
% ==================================================
\newcommand{\structsection}[1]{%
  \clearpage
  {\centering\fontsize{14pt}{16pt}\selectfont\bfseries\MakeUppercase{#1}\par}%
  \addcontentsline{toc}{section}{\MakeUppercase{#1}}%
  \vspace{21pt}%
  \par\onehalfspacing
  \ignorespaces
}

% ==================================================
% ОГЛАВЛЕНИЕ
% ==================================================
\renewcommand{\cfttoctitlefont}{\hfill\fontsize{14pt}{16pt}\bfseries\selectfont\MakeUppercase}
\renewcommand{\cftaftertoctitle}{\hfill}
\renewcommand{\cftbeforesecskip}{0pt}
\renewcommand{\cftbeforesubsecskip}{0pt}
\renewcommand{\cftbeforesubsubsecskip}{0pt}
\AtBeginDocument{\addtocontents{toc}{\protect\setstretch{1.5}}}
\renewcommand{\cftdot}{.}
\renewcommand{\cftsecleader}{\cftdotfill{\cftdot}}
\setlength{\cftsecindent}{0pt}
\setlength{\cftsubsecindent}{1.25cm}
\renewcommand{\cftsecfont}{\bfseries\fontsize{14pt}{16pt}\selectfont}
\renewcommand{\cftsubsecfont}{\bfseries\fontsize{14pt}{16pt}\selectfont}
\renewcommand{\cftsecpagefont}{\bfseries\fontsize{14pt}{16pt}\selectfont}
\renewcommand{\cftsubsecpagefont}{\bfseries\fontsize{14pt}{16pt}\selectfont}

% ==================================================
% ПОДПИСИ
% ==================================================
\DeclareCaptionLabelSeparator{emdash}{\space\textemdash\space}
\DeclareCaptionFont{captionfont}{\fontsize{12pt}{14pt}\selectfont}

\addto\captionsrussian{
  \renewcommand{\figurename}{Рисунок}
  \renewcommand{\tablename}{Таблица}
  \renewcommand{\lstlistingname}{Листинг}
}

\captionsetup[lstlisting]{labelsep=emdash,font=captionfont,justification=raggedright,singlelinecheck=false}
\captionsetup[figure]{labelsep=emdash,font=captionfont,aboveskip=12pt,belowskip=0pt}
\captionsetup[table]{position=above,labelformat=default,labelsep=endash,justification=raggedright,font=captionfont,skip=6pt}

% ==================================================
% ЛИСТИНГИ
% ==================================================
\lstset{
  basicstyle=\ttfamily\fontsize{10pt}{12pt}\selectfont,
  numbers=left,
  numberstyle=\fontsize{10pt}{12pt}\selectfont,
  numbersep=0.75em,
  xleftmargin=2.2em,
  frame=leftline,
  breaklines=true,
  tabsize=2,
  showstringspaces=false,
  backgroundcolor=\color{white},
  aboveskip=0pt,
  belowskip=0pt,
  captionpos=t,
  extendedchars=true,
  inputencoding=utf8,
  keepspaces=true,
  stringstyle=\ttfamily,
}

\newcommand{\insertlisting}[3][]{%
  \vspace{21pt}%
  \ifthenelse{\isempty{#1}}%
    {\begin{lstlisting}[label={#2}]}%
    {\begin{lstlisting}[caption={#1}, label={#2}]}%
#3
  \end{lstlisting}%
  \vspace{21pt}%
}

% ==================================================
% ИЗОБРАЖЕНИЯ
% ==================================================
\newcommand{\insertimage}[3][1]{
  \vspace{21pt}
  \begin{figure}[H]
    \centering
    \includegraphics[scale=#1]{#2}
    \caption{#3}
    \label{#2}
  \end{figure}
  \vspace{21pt}
}

% ==================================================
% ТАБЛИЦЫ
% ==================================================
\newcommand{\inserttable}[3][]{%
  \vspace{21pt}%
  \begin{table}[H]
    \centering
    \begin{tabularx}{\textwidth}{#2}
      #3
    \end{tabularx}
    \ifthenelse{\isempty{#1}}{}{\caption{#1}}%
    \label{tab:#1}
  \end{table}
  \vspace{21pt}
}

% ==================================================
% МАКРОСЫ ДЛЯ ССЫЛОК НА ОБЪЕКТЫ
% ==================================================
\newcommand{\figref}[1]{рис.~\ref{#1}}
\newcommand{\tabref}[1]{табл.~\ref{#1}}
\newcommand{\lstref}[1]{листинг~\ref{#1}}

% ==================================================
% СПИСКИ
% ==================================================
\setlist{nosep, topsep=0pt, itemsep=0pt, parsep=0pt}
\setlist[itemize]{label=\textendash,labelsep=0.35em,labelwidth=0.6em,labelindent=0cm,leftmargin=!,itemindent=0pt,listparindent=0pt,align=parleft}
\setlist[enumerate]{label=\arabic*.,leftmargin=1.25cm,labelsep=0.5em,itemsep=0pt,topsep=0pt}

% ==================================================
% CSV-Таблицы (для будущего)
% ==================================================
\RequirePackage{csvsimple}
\RequirePackage{adjustbox}
\RequirePackage{booktabs}
\newcolumntype{Y}{>{\centering\arraybackslash}X}
\newcolumntype{C}[1]{>{\centering\arraybackslash}m{#1}}

\newenvironment{csvtable}[3][]{%
  \vspace{12pt}%
  \noindent%
  \begin{adjustbox}{max width=\textwidth,#1}%
    \renewcommand{\arraystretch}{1.5}%
    \fontsize{12pt}{14pt}\selectfont%
    \setlength{\tabcolsep}{4pt}%
    \begin{tabular}{|" + *{\csvcolcount}{C{1.5cm}|} + "}%
      \hline
      #3 \\ \hline
      \csvreader[head to column names, late after line=\\\hline, late after last line=\\\hline]{#2}{}%
        {%
          \csvcoli & \csvcolii & \csvcoliii & \csvcoliv & \csvcolv & \csvcolvi & \csvcolvii & \csvcolviii & \csvcolix & \csvcolx%
        }%
}{%
    \end{tabular}%
  \end{adjustbox}%
  \vspace{12pt}%
}

% ==================================================
% ПЕРЕНОСЫ СЛОВ
% ==================================================
\frenchspacing
\sloppy
\hyphenpenalty=10000
