# Changelog

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

---

## v1.7.2 (31/08/2023)
## Changes
## 🐛 Hotfixes

- Fix vulnerability from requirements.txt @JustinWonjaePark (#138)

---

## v1.7.1 (31/08/2023)
## Changes
## 🔧 Maintenance

- Priority change between Download Location extraction and scanner operation @JustinWonjaePark (#133)

---

## v1.7.0 (14/08/2023)
## Changes
- Fix the bug when nothing is detected @soimkim (#134)

## 🚀 Features

- Load v32 and later of ScanCode @soimkim (#131)

## 🔧 Maintenance

- Fix the scancdoe and util version @dd-jy (#132)

---

## v1.6.32 (03/08/2023)
## Changes
## 🐛 Hotfixes

- Fix the util version @dd-jy (#130)

---

## v1.6.31 (03/08/2023)
## Changes
## 🐛 Hotfixes

- Revert the scancode-toolkit version @dd-jy (#129)

## 🔧 Maintenance

- Remove sorting @JustinWonjaePark (#128)

---

## v1.6.30 (25/07/2023)
## Changes
## 🔧 Maintenance

- Update scancode-toolkit version @dd-jy (#127)

---

## v1.6.29 (25/07/2023)
## Changes
## 🚀 Features

- Read download location @JustinWonjaePark (#124)

## 🐛 Hotfixes

- Update FOSSLight Util version @soimkim (#126)

## 🔧 Maintenance

- Sort the result by file and exclude attributes @JustinWonjaePark (#125)
- Update the minimum version of util @dd-jy (#123)
- Change the default path to find sbom-info.yaml @dd-jy (#122)

---

## v1.6.28 (02/06/2023)
## Changes
## 🔧 Maintenance

- Update the minimum version of util @dd-jy (#123)
- Change the default path to find sbom-info.yaml @dd-jy (#122)

---

## v1.6.27 (19/05/2023)
## Changes
## 🚀 Features

- Add to correct with sbom-info.yaml @dd-jy (#120)

## 🐛 Hotfixes

- Remove empty scanoss reference @JustinWonjaePark (#119)

## 🔧 Maintenance

- Fixed scancode-toolkit version @dd-jy (#118)

---

## v1.6.26 (17/04/2023)
## Changes
## 🐛 Hotfixes

- Update the ubuntu version for deploy action @dd-jy (#117)
- Remove SPDX, URL from copyright @soimkim (#115)

## 🔧 Maintenance

- Fix Scancode error in Python 3.7 @soimkim (#116)

---

## v1.6.25 (27/02/2023)
## Changes
## 🔧 Maintenance

- Update git user in release action @bjk7119 (#114, #113)
- Add the package name to result in the missing file @dd-jy (#112)
- Add the package name to log and result file @dd-jy (#111)
- Add the core option in help message @dd-jy (#110)
- Unify version output format @bjk7119 (#109)
- Change package to get release package @bjk7119 (#108)
- Update version of packages for actions @bjk7119 (#107)

---

## v1.6.24 (02/01/2023)
## Changes
## 🐛 Hotfixes

- Fix omitted Scanoss result at -m option @JustinWonjaePark (#106)
- Remove warning for -m option with default output @JustinWonjaePark (#104)

## 🔧 Maintenance

- Remove warranty-disclaimer from license detected by ScanCode @JustinWonjaePark (#105)
- Revert "Fix ScanCode's import LegacyVersion bug" @soimkim (#103)

---

## v1.6.23 (23/12/2022)
## Changes
## 🔧 Maintenance

- Revert "Clear ScanCode cache after installation" @soimkim (#102)

---

## v1.6.22 (23/12/2022)
## Changes
## 🐛 Hotfixes

- Clear ScanCode cache after installation @soimkim (#101)

---

## v1.6.21 (08/12/2022)
## Changes
## 🔧 Maintenance

- Add parameter for Scancode cores @soimkim (#100)

---

## v1.6.20 (18/11/2022)
## Changes
## 🐛 Hotfixes

- Block -m option for opossum,yaml and csv @JustinWonjaePark (#98)
