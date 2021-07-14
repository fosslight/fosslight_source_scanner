<!--
Copyright (c) 2021 LG Electronics
SPDX-License-Identifier: Apache-2.0
 -->
<p align='right'>
  <a href="https://fosslight.org/fosslight-guide/scanner/1_source.html">
    [Korean]
 </a>
</p>

# FOSSLight Source Scanner

<img src="https://img.shields.io/pypi/l/fosslight_source" alt="FOSSLight Source Scanner is released under the Apache-2.0 License." /> <img src="https://img.shields.io/pypi/v/fosslight_source" alt="Current python package version." /> <img src="https://img.shields.io/pypi/pyversions/fosslight_source" /> [![REUSE status](https://api.reuse.software/badge/github.com/fosslight/fosslight_source_scanner)](https://api.reuse.software/info/github.com/fosslight/fosslight_source_scanner) [![Guide](http://img.shields.io/badge/-doc-blue?style=flat-square&logo=github&link=https://fosslight.org/fosslight-guide-en/scanner/1_source.html)](https://fosslight.org/fosslight-guide-en/scanner/1_source.html)
</p>

```note
Detect the license for the source code.
Use Source Code Scanner and process the scanner results.
```

**FOSSLight Source Scanner** uses [ScanCode][sc], a source code scanner, to detect the copyright and license phrases contained in the file. Some files (ex- build script), binary files, directory and files in specific directories (ex-test) are excluded from the result. And removes words such as "-only" and "-old-style" from the license name to be printed. The output result is generated in Excel format.


[sc]: https://github.com/nexB/scancode-toolkit


## 📖 User Guide

We describe the user guide in the FOSSLight guide page.
Please see the [**User Guide**](https://fosslight.org/fosslight-guide-en/scanner/1_source.html) for more information on how to install and run it.


## 👏 Contributing Guide

We always welcome your contributions.  
Please see the [CONTRIBUTING guide](https://fosslight.org/fosslight-guide-en/learn/1_contribution.html) for how to contribute.


## 📄 License

FOSSLight Source Scanner is Apache-2.0, as found in the [LICENSE][l] file.

[l]: https://github.com/fosslight/fosslight_source_scanner/blob/main/LICENSE
