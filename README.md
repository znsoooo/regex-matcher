# regex-matcher
Search regex matched in text in GUI interface


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


## 3. Specification

### 3.1 Open / Save
- Open multiple `*.txt` files and show in `Text` window
- Save current text in `Text` window to local disk

### 3.2 RegEx / Replace
- In `RegEx` mode, input pattern and find matches in `Text` and show in `Result` window
- In `Replace` mode, input pattern and replace to replace text in `Text` window

### 3.3 Sorted / Unique
- Sort found items and show in `Result` window
- Remove duplicate item in `Result` window

### 3.4 Prev / Next
- View previous / next match position in `Text` window

### 3.5 Apply
- Use current `Result` window's text to replace `Text` window
