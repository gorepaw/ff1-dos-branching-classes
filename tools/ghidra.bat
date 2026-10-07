@echo off
rem Launch the local Ghidra with the local JDK 21 (run tools\setup.py --ghidra first).
set "BIN=%~dp0bin"
for /d %%J in ("%BIN%\jdk21\jdk-*") do set "JAVA_HOME=%%J"
for /d %%G in ("%BIN%\ghidra\ghidra_*") do set "GHIDRA=%%G"
set "PATH=%JAVA_HOME%\bin;%PATH%"
start "" "%GHIDRA%\ghidraRun.bat"
