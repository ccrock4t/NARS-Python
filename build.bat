set condapath="C:\Users\%USERNAME%\Anaconda3"
call %condapath%\Scripts\activate.bat %condapath%
call activate NARS-Python
set NARS_ROOT=%cd%
cd %NARS_ROOT%
pyinstaller --onefile main.py
cmd \k