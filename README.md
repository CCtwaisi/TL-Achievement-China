School Principals’ Transformational Leadership and Student Academic Achievement in Chinese Middle Schools — Systematic Review & Meta-analysis
DOI（占位）：https://doi.org/10.5281/zenodo.TBD
Docs 许可：CC BY 4.0（https://creativecommons.org/licenses/by/4.0/）
Code 许可：MIT（参见仓库 LICENSE 文件）
Author：LUO XI（University of Malaya）
Protocol version：v1.0（July 12, 2025）
Overview
This repository hosts the PRISMA-compliant protocol, data templates, and analysis scaffolding for a systematic review and meta-analysis on the association between principals’ transformational leadership (TL) and students’ academic achievement in Chinese middle schools.
Primary Question（RQ1）：Is principals’ TL positively associated with student academic achievement?
Moderators（RQ2）：Region（east/central/west; urban/rural）, measurement instrument（MLQ/TLQ/other）, publication year, and sample level（student/class/school）.
Designs Included：Quantitative empirical studies（correlational, regression, group comparison, panel/longitudinal, quasi-experimental）.
Primary Effect Size：Pearson r, transformed to Fisher’s z; random-effects（REML）, with heterogeneity, prediction interval, bias diagnostics, and sensitivity analyses.
Project website（GitHub Pages）：https://cctwaisi.github.io/TL-Achievement-China/
Downloads（protocol files）
Place these files into the repo under the docs/ folder so the links work both on GitHub and on the Pages site.
Protocol（EN, PDF, final）：docs/Protocol_v1.0_PRISMA_EN_FINAL_2025-07-12.pdf
Protocol（EN, DOCX, final）：docs/Protocol_v1.0_PRISMA_EN_FINAL_2025-07-12.docx
Protocol（Bilingual CN–EN, DOCX, final）：docs/Protocol_v1.0_PRISMA_Bilingual_CN-EN_FINAL_2025-07-12.docx
（Optional）You may also include Chinese-only documentation and templates in docs/.
Repository structure（suggested）
/
├─ docs/ Website content and downloadable protocol files（served by GitHub Pages）
│ ├─ index.md Project homepage（auto-built by Pages）
│ ├─ Protocol_v1.0_*.pdf/docx
│ └─ assets/ Images（PRISMA, forest/funnel plots）for the site
├─ code/ R scripts（metafor, clubSandwich）and reproducible pipelines
│ ├─ 00_setup.R
│ ├─ 10_extract_convert_effects.R
│ ├─ 20_meta_main_REML.R
│ ├─ 30_subgroups_meta_regression.R
│ ├─ 40_publication_bias_sensitivity.R
│ └─ 90_make_figures_tables.R
├─ data_raw/ Search exports（CSV/RIS）, PDFs
├─ data_clean/ Curated tables（Study_Characteristics.csv, effects.csv, RoB tables）
├─ figures/ PRISMA flow, forest/funnel plots
├─ tables/ Summary tables, moderator results, RoB summaries
├─ manuscript/ Write-up and appendices
├─ protocol/ PRISMA checklist, working drafts
└─ README.md
Getting started（analysis workflow）
1.Clone the repo and open code/00_setup.R to install/load required packages（metafor, clubSandwich, tidyverse）.
2.Place search exports into data_raw/ and run 10_extract_convert_effects.R to build data_clean/effects.csv.
3.Run 20_meta_main_REML.R for the main random-effects synthesis and heterogeneity diagnostics.
4.Run 30_subgroups_meta_regression.R for moderator analyses.
5.Run 40_publication_bias_sensitivity.R for Egger, trim-and-fill, leave-one-out, and influence diagnostics.
6.Generate figures/tables with 90_make_figures_tables.R and include them under docs/assets/ for the website.
GitHub Pages（project website）
This repo includes a ready-to-use docs/index.md homepage. To enable the website：
Settings → Pages → Build and deployment
Source：Deploy from a branch
Branch：main → /docs
Save. Your site will be published at：https://cctwaisi.github.io/TL-Achievement-China/
DOI via Zenodo
1.Sign in to Zenodo and connect your GitHub account.
2.In Zenodo, enable archiving for this repository.
3.Back on GitHub, create a Release（for example v1.0）and attach the PDF/DOCX protocol files.
4.Zenodo will mint a DOI automatically. Replace the placeholder in this README and on the website with the real DOI（for example 10.5281/zenodo.1234567）.

DOI badge image URL template：https://zenodo.org/badge/DOI/10.5281/zenodo.1234567.svg
DOI landing page：https://doi.org/10.5281/zenodo.1234567
How to cite
APA example（update DOI after minting）：
Luo, X.（2025）. Protocol v1.0：School Principals’ Transformational Leadership and Student Academic Achievement in Chinese Middle Schools — A Systematic Review and Meta-analysis（Version 1.0）[Protocol]. University of Malaya. https://doi.org/10.5281/zenodo.TBD
License
Text and documents：CC BY 4.0
Code：MIT
Contact
LUO XI — University of Malaya
Issues and pull requests are welcome.
中文快速导航（可选）
协议下载：见 docs 文件夹（PDF 和 DOCX）。
网站发布：Settings → Pages → Branch：main / Folder：/docs。
DOI：Zenodo 连接 GitHub，发布 Release 后自动生成；把 DOI 徽章与引用更新到 README 与页面顶部。
目录结构：code（R 脚本）、data_raw（题录与 PDF）、data_clean（整理表）、figures（森林、漏斗、PRISMA）、tables（汇总表）、docs（网站与下载）。
