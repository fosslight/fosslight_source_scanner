# Changelog

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

---

## v2.1.13 (10/09/2025)
## Changes
## 🔧 Maintenance

- Add is_manifest_file field @dd-jy (#215)

---

## v2.1.12 (21/08/2025)
## Changes
## 🚀 Features

- Exclude package dirs with directory name @dd-jy (#214)

## 🔧 Maintenance

- Fix scancode version for Mac @JustinWonjaePark (#213)

---

## v2.1.11 (21/07/2025)
## Changes
## 🔧 Maintenance

- Remove copyright info for license text file of GPL family @JustinWonjaePark (#212)

---

## v2.1.10 (17/07/2025)
## Changes
- Recognize manifest file as License File @JustinWonjaePark (#210)

## 🔧 Maintenance

- Update Python support to 3.10+ and remove scanners' version limits @JustinWonjaePark (#211)

---

## v2.1.9 (10/07/2025)
## Changes
- Remove copyright from SCANOSS result @JustinWonjaePark (#209)

## 🔧 Maintenance

- Fix github action warning message @bjk7119 (#208)

---

## v2.1.8 (09/04/2025)
## Changes
## 🔧 Maintenance

- Fix api_limit_exceed_parameter @JustinWonjaePark (#206)

---

## v2.1.7 (26/02/2025)
## Changes
## 🔧 Maintenance

- Update SCANOSS version and redirect log @JustinWonjaePark (#204)

---

## v2.1.6 (06/02/2025)
## Changes
## 🐛 Hotfixes

- Fix scancode copyright scanning err @dd-jy (#203)
- Fix exclude error @JustinWonjaePark (#201)

---

## v2.1.5 (09/12/2024)
## Changes
## 🐛 Hotfixes

- Fix the bug @dd-jy (#200)

---

## v2.1.4 (05/12/2024)
## Changes
## 🚀 Features

- Support cycloneDX format @dd-jy (#199)

---

## v2.1.3 (13/11/2024)
## Changes
- Fix errors related to SCANOSS @JustinWonjaePark (#198)

## 🔧 Maintenance

- Fix the cover_comment @ethanleelge (#197)
