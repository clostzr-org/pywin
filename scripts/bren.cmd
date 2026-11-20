@echo off
setLocal enableDelayedExpansion
title %CD%
@py "%~dpn0.py" %* 