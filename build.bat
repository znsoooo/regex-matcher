@echo off

set name=RegexMatcher

pyinstaller -ywsF --noupx %name%.py --icon icon.ico --add-data=icon.ico;.
echo.

pyinstaller -yws --noupx %name%.py --icon icon.ico --add-data=icon.ico;.
echo.

dist\%name%\%name%.exe
pause
