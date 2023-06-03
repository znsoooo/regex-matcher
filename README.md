# regex-matcher

- Using GUI to apply RegEx matching or replacement for the text.
- Input RegEx and highlight the matching results in real-time in the `Text` window, support multi-groups.
- The matches are displayed in the `Result` window, separated by `Tab`, can be copied to `Excel` sheet.
- Use the `Sorted` or `Unique` switch to filter the results.


## 1. About
- __Author:__ Lishixian
- __QQ:__ 11313213
- __Email:__ <lsx7@sina.com>
- __GitHub:__ <https://github.com/znsoooo/regex-matcher>
- __License:__ MIT License. Copyright (c) 2023 Lishixian (znsoooo). All Rights Reserved.


## 2. Usage
```shell
pip install wxPython>=4.0.0
python RegexMatcher.py
```


## 3. App Interface
```
+----------------------------------------------------------------+
| Regex Matcher v1.0.0                               [_] [ ] [X] |
+---------------------------------+------------------------------+
| Text:                           | Result:                      |
|                                 |                              |
| The quick brown fox jumps over  | quick                        |
| the lazy dog.                   | brown                        |
|                                 | jumps                        |
|                                 |                              |
|                                 |                              |
|                                 +----------------------+---+---+
|                                 | RegEx:   [ \w{5}   ] | < | > +
|                                 +----------------------+---+---+
|                                 | Replace: [         ] | Apply |
+---------------------------------+----------------------+-------+
```


## 4. Specification

### 4.1 RegEx / Replace
- Input pattern in `RegEx` box, find matches in `Text` and show in `Result` window
- Input template in `Replace` box, show replaced text in `Result` window

### 4.2 Sorted / Unique
- Sort found items and show in `Result` window
- Remove duplicate item in `Result` window

### 4.3 Prev / Next
- View previous / next matched position in `Text` window

### 4.4 Apply
- Use current `Result` window's text to replace `Text` window
