@echo off
setlocal
rem === Cari proses python/pythonw yang menjalankan main.py aplikasi ini dan matikan ===
powershell -NoProfile -Command ^
  "$procs = Get-CimInstance Win32_Process | Where-Object { $_.Name -match 'python' -and $_.CommandLine -match 'dummy-file-generator\\main\.py' };" ^
  "if ($procs) { foreach ($p in $procs) { Stop-Process -Id $p.ProcessId -Force; Write-Host ('Stopped PID ' + $p.ProcessId) } }" ^
  "else { Write-Host 'Tidak ada proses Dummy File Generator yang berjalan.' }"
exit /b 0
