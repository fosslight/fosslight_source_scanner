# Changelog

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

---

## v2.1.2 (18/10/2024)
## Changes
## 🔧 Maintenance

- Print option name with error msg @bjk7119 (#195)
- Fix the scancode ver for macos @dd-jy (#194)

---

## v2.1.1 (13/10/2024)
## Changes
## 🔧 Maintenance

- Remove typecode-libmagic from requirements.txt @soonhong99 (#192)

---

## v2.1.0 (08/10/2024)
## Changes
## 🚀 Features

- Support spdx (only Linux) @dd-jy (#190)

## 🔧 Maintenance

- Tox to pytest @hkkim2021 (#188)
- Add type hint @hkkim2021 (#184)

---

## v2.0.0 (06/09/2024)
## Changes
## 🔧 Maintenance

- Refactoring OSS Item @soimkim (#183)

---

## v1.7.16 (06/09/2024)
## Changes
## 🔧 Maintenance

- Limit installation to fosslight_util 1.4.* @soimkim (#182)
- Change SCANOSS Invocation Method from Command Line to Library Function @YongGoose (#178)
- Modify error comment @bjk7119 (#176)
- Add --ignore-cert-errors to ScanOSS command @soimkim (#174)

---

## v1.7.15 (17/07/2024)
## Changes
## 🐛 Hotfixes

- Version up FOSSLight util to fix default file bug @JustinWonjaePark (#170)
- Complying with SPDX License expression spec @JustinWonjaePark (#167)

---

## v1.7.14 (15/07/2024)
## 🚀 Features

- Enable multiple input for -f and -o option @JustinWonjaePark (#164)

## 🐛 Hotfixes

- Update scancode version for mac @soimkim (#168)
- Fix SPDX expression split bug @JustinWonjaePark (#165)
- Revert "Fix SPDX expression split bug" @soimkim (#169)

## 🔧 Maintenance

- Check hidden files and mark 'Exlcude'. @JustinWonjaePark (#166)

---

## v1.7.13 (25/06/2024)
## Changes
## 🐛 Hotfixes

- Amend exclude option @SeongjunJo (#162)

---

## v1.7.12 (21/06/2024)
## Changes
## 🔧 Maintenance

- Update scancode version for web service @soimkim (#161)

---

## v1.7.11 (11/06/2024)
## Changes
## 🐛 Hotfixes

- Bug fix related to license duplication @soimkim (#159)

## 🔧 Maintenance

- Check empty license @soimkim (#160)

---

## v1.7.10 (11/06/2024)
## Changes
## 🐛 Hotfixes

- Move method to limit license characters @soimkim (#158)

---

## v1.7.9 (11/06/2024)
## Changes
## 🔧 Maintenance

- Limit the maximum number of characters in the license @soimkim (#157)

---

## v1.7.8 (10/06/2024)
## Changes
## 🚀 Features

- Supports for excluding paths @SeongjunJo (#154)

## 🔧 Maintenance

- Modify column name @bjk7119 (#156)
- Change column name for SCANOSS reference @JustinWonjaePark (#155)

---

## v1.7.7 (26/04/2024)
## Changes
## 🚀 Features

- Add detection summary message (cover sheet) @dd-jy (#153)

## 🔧 Maintenance

- Check notice file name for scancode @JustinWonjaePark (#152)

---

## v1.7.6 (29/02/2024)
## Changes
## 🐛 Hotfixes

- Fix cli_test log path @JustinWonjaePark (#148)

## 🔧 Maintenance

- Change SCANOSS thread using -c option @JustinWonjaePark (#151)
- Remove fosslight_convert @JustinWonjaePark (#150)

---

## v1.7.5 (19/10/2023)
## Changes
## 🔧 Maintenance

- Merge copyrights with new line @JustinWonjaePark (#147)
- Add .in and .po to the excluded extensions @JustinWonjaePark (#146)

---

## v1.7.4 (13/10/2023)
## Changes
- Optimize Dockerfile to reduce image size @jaehee329 (#136)

## 🐛 Hotfixes

- Modify it to work on mac ARM chip @soimkim (#145)

## 🔧 Maintenance

- Upgrade minimum version of python to 3.8 @JustinWonjaePark (#144)
- Modify run_scanners to return @soimkim (#143)
- Fetch base-check-commit-message.yml from .github @jaehee329 (#142)

---

## v1.7.3 (14/09/2023)
## Changes
## 🔧 Maintenance

- Create run_scanners for api and exclude unwanted outputs @JustinWonjaePark (#140)
- Add test for fl scanner and fl android @JustinWonjaePark (#139)
