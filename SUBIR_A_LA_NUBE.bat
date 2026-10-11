@echo off
chcp 65001 >nul
title Subir el MOTOR a la nube - TECNO G
color 0B
cd /d "%~dp0"

echo ============================================================
echo   SUBIR EL MOTOR DE IA A TU NUBE  (desde Windows)
echo ============================================================
echo.
echo  Esto copia TODA esta carpeta a tu servidor con GPU por SSH.
echo.
echo  Necesitas:
echo    - La IP de tu nube
echo    - El usuario (ej: root, ubuntu, fer)
echo    - La contrasena o una clave SSH configurada
echo.
echo ------------------------------------------------------------

set /p USUARIO=Usuario de la nube (ej: root):
set /p HOST=IP o dominio de la nube:
set /p DESTINO=Carpeta destino (Enter = /root/MOTOR_COMPLETO):
if "%DESTINO%"=="" set DESTINO=/root/MOTOR_COMPLETO

echo.
echo Subiendo a %USUARIO%@%HOST%:%DESTINO% ...
echo.

where scp >nul 2>nul
if %errorlevel%==0 (
  ssh %USUARIO%@%HOST% "mkdir -p %DESTINO%"
  scp -r * %USUARIO%@%HOST%:%DESTINO%/
) else (
  where pscp >nul 2>nul
  if %errorlevel%==0 (
    echo Usando pscp (PuTTY)...
    pscp -r * %USUARIO%@%HOST%:%DESTINO%/
  ) else (
    echo [!] No encontre 'scp' ni 'pscp' en tu PC.
    echo.
    echo Opciones:
    echo   1) Instala OpenSSH: Panel de control ^> Aplicaciones ^> Caracteristicas opcionales
    echo   2) O usa WinSCP (grafico): https://winscp.net
    echo   3) O instala PuTTY (trae pscp): https://putty.org
    echo.
    pause
    exit /b 1
  )
)

echo.
echo ============================================================
echo  LISTO. El codigo esta en tu nube.
echo.
echo  AHORA conectate por SSH y corre el instalador:
echo     ssh %USUARIO%@%HOST%
echo     cd %DESTINO%
echo     bash instalar_motor.sh
echo ============================================================
echo.
pause
