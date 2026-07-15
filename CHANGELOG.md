# Changelog

## v2.3.5 (15/07/2026)
## Changes
## 🚀 Features

- Skip binaries via scancode-ignore-binaries @soimkim (#296)

## 🔧 Maintenance

- feat: support and log timeout for SCANOSS scannerFeat/set scanoss timeout @JustinWonjaePark (#297)
- Mark manifest files in UI mode without requiring licenses @soimkim (#295)
- Keep copyright findings without full-file ScanCode output @soimkim (#294)
- Skip ScanCode only-findings when --ui is set @soimkim (#293)
- Keep ScanOSS OSS identity when ScanCode has license @soimkim (#292)

---

## v2.3.4 (13/07/2026)
## Changes
## 🐛 Hotfixes

- Require lxml>=6.0.1 for Python 3.14 wheel support @soimkim (#290)

## 🔧 Maintenance

- Optimize scancode ignore pattern size using wildcards @JustinWonjaePark (#288)
- Hide KB response counts in Scanner Info and show Completed status. @soimkim (#291)

---

## v2.3.3 (09/07/2026)
## Changes
## 🚀 Features

- Add folder summary for source report @JustinWonjaePark (#278)

## 🔧 Maintenance

- Unify running time formatting in reports and logs @bjk7119 (#286)
- Migrate to REUSE.toml and update GitHub Action @woocheol-lge (#287)

---

## v2.3.2 (30/06/2026)
## Changes
## 🔧 Maintenance

- Report scan job create failures on Cover sheet @soimkim (#285)

---

## v2.3.1 (29/06/2026)
## Changes
## 🐛 Hotfixes

- Use path-based ignore globs for directory excludes @soimkim (#283)

## 🔧 Maintenance

- Cleanup .fosslight_temp_{start_time} on scan interrupt @soimkim (#284)
- Skip hash collection for files with download_location @soimkim (#282)

---

## v2.3.0 (25/06/2026)
## Changes
## 🚀 Features

- Switch KB lookup from query to scan jobs polling @soimkim (#277)

## 🐛 Hotfixes

- Fix refine regex pattern for parsing custom license @JustinWonjaePark (#280)
- Fix release CI failures from cryptography and pytest-flake8 @JustinWonjaePark (#279)

## 🔧 Maintenance

- Print kb server message on Cover sheet @soimkim (#281)

---

## v2.2.17 (05/06/2026)
## Changes
## 🔧 Maintenance

- Reduce scancode ignore patterns with coarse exclude globs @soimkim (#276)

---

## v2.2.16 (28/05/2026)
## Changes
## 🚀 Features

- Support configurable KB URL and bearer token @soimkim (#273)
- Add license extraction for pyproject.toml @JustinWonjaePark (#270)

## 🐛 Hotfixes

- Prevent mutation of shared excluded_files list @bjk7119 (#275)

## 🔧 Maintenance

- Exclude OSS info correction files @JustinWonjaePark (#271)

---

## v2.2.15 (30/04/2026)
## 🚀 Features
- Support Hugging Face metadata license extraction in manifest flow @soimkim (#269)

## 🔧 Maintenance
- [Snyk] Security upgrade pyopenssl from 25.3.0 to 26.0.0 @bjk7119 (#266)
- Add scanner version log at startup @woocheol-lge (#268)
- Remove pyopenssl pin from requirements-dev.txt @bjk7119 (#267)

---

## v2.2.14 (31/03/2026)
## Changes
## 🚀 Features

- Ignore binaries during ScanCode scan @soimkim (#265)

## 🔧 Maintenance

- Add --hide_progress command-line flag to suppress progress bar @soimkim (#264)

---

## v2.2.13 (26/03/2026)
## Changes
## 🔧 Maintenance

- refactor(build): use SPDX license expression in pyproject.toml @soimkim (#262)
- feat(python): add Python 3.13/3.14 support @soimkim (#261)
- refactor(build): migrate from setup.py to pyproject.toml @soimkim (#260)

---

## v2.2.12 (19/03/2026)
## Changes
## 🐛 Hotfixes

- fix(scancode): handle Click 8.3+ UNSET in plugin options to avoid Sentinel errors @soimkim (#259)

---

## v2.2.11 (12/03/2026)
## Changes
## 🚀 Features

- Add kb_reference sheet and KB-only analysis mode @soimkim (#257)

---

## v2.2.10 (09/03/2026)
## Changes
## 🔧 Maintenance

- Remove kb from all mode @soimkim (#254)

---

## v2.2.9 (08/03/2026)
## Changes
## 🔧 Maintenance

- Remove "Type of change" section from PR default template @woocheol-lge (#252)
- Refactor logging to use debug for error related API calls @soimkim (#251)

---

## v2.2.8 (26/02/2026)
## Changes
## 🔧 Maintenance

- Add initial coderabbit configuration @soimkim (#250)
- Retrieve SPDX from a given license @soimkim (#249)

---

## v2.2.7 (23/02/2026)
## Changes
## 🐛 Hotfixes

- Fix Scancode's dependency package bug @soimkim (#248)

---

## v2.2.6 (13/02/2026)
## Changes
## 🚀 Features

- Add snippet matching to FOSSLight KB @soimkim (#245)

---

## v2.2.5 (05/02/2026)
## Changes
## 🐛 Hotfixes

- Fix bug while removing temp files @JustinWonjaePark (#244)

---

## v2.2.4 (02/02/2026)
## Changes
## 🐛 Hotfixes

- Fix intermediate file path bug @JustinWonjaePark (#243)

## 🔧 Maintenance

- Update help message @bjk7119 (#241)
- Update temporary directory name @soimkim (#242)

---

## v2.2.3 (23/01/2026)
## Changes
- Fix tox.ini @JustinWonjaePark (#237)

## 🐛 Hotfixes

- Use hidden dir for intermeditate to fix scan count @JustinWonjaePark (#234)

## 🔧 Maintenance

- Update Scanner Info sheet and fix bug related to temp directory @JustinWonjaePark (#236)
- Take UNLICENSED expression from npmjs @JustinWonjaePark (#239)
- Fix logging @JustinWonjaePark (#238)
- Replace exclusion to FL Util @soimkim (#235)
- Remove duplicated exclude logic for all mode @dd-jy (#240)

---

## v2.2.2 (19/01/2026)
## Changes
## 🚀 Features

- Add license extraction for package.json and setup.py,cfg @JustinWonjaePark (#233)
- Add manifest extractor @JustinWonjaePark (#232)

---

## v2.2.1 (14/01/2026)
## Changes
## 🔧 Maintenance

- Remove files from Scancode @soimkim (#231)
- Replace list to set @soimkim (#230)
- Replace exclude function to fosslight_util @soimkim (#229)

---

## v2.2.0 (09/01/2026)
## Changes
- Print comment only if OR is included @soimkim (#227)

## 🚀 Features

- Add KB to Scanner Type @soimkim (#221)

## 🐛 Hotfixes

- Remove source files from license text @soimkim (#228)

## 🔧 Maintenance

- Remove duplication in skipped path @soimkim (#226)

---

## v2.1.19 (07/01/2026)
## Changes
## 🐛 Hotfixes

- Update fosslight_util minimun version @dd-jy (#225)

---

## v2.1.18 (07/01/2026)
## Changes
## 🐛 Hotfixes

- Improve path exclusion handling in scancode @soimkim (#222)

## 🔧 Maintenance

- Add how to use -e option @bjk7119 (#223)
- Exclude default paths from ScanCode @soimkim (#224)

---

## v2.1.17 (24/12/2025)
## Changes
## 🔧 Maintenance

- Update supported format @dd-jy (#220)

---

## v2.1.16 (12/12/2025)
## Changes
- Double-Check pom file license with license tag @dd-jy (#219)

---

## v2.1.15 (01/12/2025)
## Changes
## 🐛 Hotfixes

- Fix pkg dir exclude bug for windows @dd-jy (#218)

---

## v2.1.14 (24/09/2025)
## Changes
## 🐛 Hotfixes

- Fix a click version to fix non-boolean flag error @soimkim (#217)
