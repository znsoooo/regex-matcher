@echo off

set name=RegexMatcher
set root=dist\%name%
set libs=%root%\wx

pyinstaller -ywsF --noupx %name%.py --icon icon.ico --add-data=icon.png;.
echo.

pyinstaller -yws --noupx %name%.py --icon icon.ico --add-data=icon.png;.
echo.

del  %root%\%name%.exe.manifest
echo.

move %root%\*.pyd %libs%
move %root%\*.dll %libs%
move %libs%\python*.dll %root%
echo.

%root%\%name%.exe
pause
