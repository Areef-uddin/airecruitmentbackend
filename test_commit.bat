@echo off
cd /d "c:\Users\home\Documents\djanolearning\New folder (2)\ai_recruitment\backend"
git add . > git_out.txt 2>&1
git commit -m "fix: remove localhost redirect and switch to neon postgresql" >> git_out.txt 2>&1
echo Commit step finished. >> git_out.txt
