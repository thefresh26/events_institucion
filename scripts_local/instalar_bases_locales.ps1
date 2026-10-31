<#
  Conexion Escolar - instala y carga las bases de datos locales (PostgreSQL + MySQL).
  Uso (PowerShell COMO ADMINISTRADOR, desde la carpeta del proyecto):
      Set-ExecutionPolicy -Scope Process Bypass -Force
      .\scripts_local\instalar_bases_locales.ps1
  Pide las contrasenas por teclado; no guarda ninguna en el script.
#>
$ErrorActionPreference = "Continue"   # los .exe escriben avisos en stderr; los errores reales se revisan con $LASTEXITCODE
$raiz = Split-Path -Parent $PSScriptRoot
$sqlPg    = Join-Path $raiz "backend\script_neon.sql"
$sqlMysql = Join-Path $raiz "aux_api\script_mysql.sql"

function Paso($t)  { Write-Host "`n=== $t" -ForegroundColor Cyan }
function Ok($t)    { Write-Host "  OK  $t" -ForegroundColor Green }
function Aviso($t) { Write-Host "  !!  $t" -ForegroundColor Yellow }
function Pedir($t) {
    $s = Read-Host $t -AsSecureString
    [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($s))
}

# --- 0) Comprobaciones -------------------------------------------------------
$admin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $admin) { throw "Abre PowerShell como Administrador (clic derecho > Ejecutar como administrador) y vuelve a correr el script." }
foreach ($f in @($sqlPg, $sqlMysql)) { if (-not (Test-Path $f)) { throw "No encuentro $f. Corre el script desde la carpeta del proyecto (events_institucion)." } }

function Buscar-Exe($nombre, $patrones) {
    $c = Get-Command $nombre -ErrorAction SilentlyContinue
    if ($c) { return $c.Source }
    foreach ($p in $patrones) {
        $r = Get-ChildItem -Path $p -ErrorAction SilentlyContinue | Sort-Object FullName -Descending | Select-Object -First 1
        if ($r) { return $r.FullName }
    }
    return $null
}

# --- 1) PostgreSQL -----------------------------------------------------------
Paso "PostgreSQL"
$psql = Buscar-Exe "psql.exe" @("C:\Program Files\PostgreSQL\*\bin\psql.exe")
if (-not $psql) {
    Aviso "No encontre PostgreSQL. Lo instalo con winget (te pedira la contrasena de 'postgres' en el instalador)."
    winget install -e --id PostgreSQL.PostgreSQL.16 --accept-package-agreements --accept-source-agreements
    $psql = Buscar-Exe "psql.exe" @("C:\Program Files\PostgreSQL\*\bin\psql.exe")
    if (-not $psql) { throw "PostgreSQL no quedo instalado. Instalalo a mano desde postgresql.org y vuelve a correr el script." }
}
Ok "psql: $psql"

# --- 2) MySQL ----------------------------------------------------------------
Paso "MySQL"
$mysql = Buscar-Exe "mysql.exe" @("C:\Program Files\MySQL\MySQL Server *\bin\mysql.exe")
if (-not $mysql) {
    Aviso "No encontre MySQL. Lo instalo con winget (descarga unos 300 MB)."
    winget install -e --id Oracle.MySQL --accept-package-agreements --accept-source-agreements
    $mysql = Buscar-Exe "mysql.exe" @("C:\Program Files\MySQL\MySQL Server *\bin\mysql.exe")
    if (-not $mysql) { throw "MySQL no quedo instalado. Instalalo con el MySQL Installer de dev.mysql.com y vuelve a correr el script." }
}
$bin = Split-Path -Parent $mysql
$mysqld = Join-Path $bin "mysqld.exe"
$base = Split-Path -Parent $bin
Ok "mysql: $mysql"

$svc = Get-Service | Where-Object { $_.Name -like "MySQL*" } | Select-Object -First 1
$primeraVez = $false
if (-not $svc) {
    Aviso "MySQL no tiene servicio de Windows todavia: lo inicializo."
    $datos = "C:\ProgramData\MySQL\data"
    $ini = Join-Path $base "my.ini"
    New-Item -ItemType Directory -Force -Path $datos | Out-Null
    $b = $base -replace "\\", "/"; $dd = $datos -replace "\\", "/"
    Set-Content -Path $ini -Value "[mysqld]`nbasedir=$b`ndatadir=$dd`nport=3306" -Encoding ASCII
    if (-not (Get-ChildItem $datos -ErrorAction SilentlyContinue)) {
        & $mysqld "--defaults-file=$ini" --initialize-insecure --console
        if ($LASTEXITCODE -ne 0) { throw "mysqld no pudo inicializar la carpeta de datos." }
    }
    & $mysqld --install MySQL80 "--defaults-file=$ini"
    $primeraVez = $true
    $svc = Get-Service -Name "MySQL80"
}
if ($svc.Status -ne "Running") { Start-Service $svc.Name; Start-Sleep -Seconds 5 }
Ok "Servicio $($svc.Name) en marcha"

# --- 3) Contrasenas ------------------------------------------------------------
Paso "Contrasenas (se piden por teclado, no se guardan en el script)"
$pgPass = Pedir "Contrasena del usuario 'postgres' de PostgreSQL"
if ($primeraVez) {
    $myPass = Pedir "Elige una contrasena para el usuario 'root' de MySQL"
    Remove-Item Env:MYSQL_PWD -ErrorAction SilentlyContinue
    & $mysql -u root --connect-expired-password -e "ALTER USER 'root'@'localhost' IDENTIFIED BY '$($myPass -replace "'", "''")';"
    if ($LASTEXITCODE -ne 0) { throw "No pude fijar la contrasena de root en MySQL." }
} else {
    $myPass = Pedir "Contrasena del usuario 'root' de MySQL"
}

# --- 4) Cargar PostgreSQL -------------------------------------------------------
Paso "Cargando base principal (PostgreSQL: conexion_escolar)"
$env:PGPASSWORD = $pgPass; $env:PGCLIENTENCODING = "UTF8"
$existe = & $psql -U postgres -h localhost -tAc "SELECT 1 FROM pg_database WHERE datname='conexion_escolar'"
if ($LASTEXITCODE -ne 0) { throw "No pude conectarme a PostgreSQL. Revisa la contrasena de 'postgres' y que el servicio este iniciado." }
if (-not $existe) { & $psql -U postgres -h localhost -c "CREATE DATABASE conexion_escolar ENCODING 'UTF8'" | Out-Null }
& $psql -U postgres -h localhost -d conexion_escolar -v ON_ERROR_STOP=1 -q -f $sqlPg
if ($LASTEXITCODE -ne 0) { throw "Fallo al cargar script_neon.sql." }
$n = & $psql -U postgres -h localhost -d conexion_escolar -tAc "SELECT count(*) FROM information_schema.tables WHERE table_schema='public'"
Ok "Tablas en PostgreSQL: $n (deben ser 18)"

# --- 5) Cargar MySQL ---------------------------------------------------------------
Paso "Cargando base auxiliar (MySQL: conexion_escolar_aux)"
$env:MYSQL_PWD = $myPass
$rutaSql = $sqlMysql -replace "\\", "/"
& $mysql -u root --default-character-set=utf8mb4 -e "source $rutaSql"
if ($LASTEXITCODE -ne 0) { throw "Fallo al cargar script_mysql.sql." }
$n2 = & $mysql -u root -N -e "SELECT count(*) FROM information_schema.tables WHERE table_schema='conexion_escolar_aux'"
Ok "Tablas en MySQL: $n2 (deben ser 4)"

# --- 6) Archivos .env (solo si no existen) ----------------------------------------------
Paso "Archivos .env"
$secreto = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 40 | ForEach-Object { [char]$_ })
$envBack = Join-Path $raiz "backend\.env"
$envAux  = Join-Path $raiz "aux_api\.env"
if (-not (Test-Path $envBack)) {
    Set-Content -Path $envBack -Encoding ASCII -Value @(
        "DB_HOST=localhost","DB_NAME=conexion_escolar","DB_USER=postgres","DB_PASSWORD=$pgPass","DB_PORT=5432","DB_SSLMODE=disable",
        "SECRET_KEY=$secreto","COOKIE_SECURE=false","FORZAR_HTTPS=false","FRONTEND_URL=http://localhost:8000")
    Ok "Cree backend\.env"
} else { Aviso "backend\.env ya existe: no lo toque. Ajusta ahi DB_NAME=conexion_escolar y tu DB_PASSWORD." }
if (-not (Test-Path $envAux)) {
    $sk = if (Test-Path $envBack) { ((Get-Content $envBack) | Where-Object { $_ -like "SECRET_KEY=*" } | Select-Object -First 1) -replace "^SECRET_KEY=", "" } else { $secreto }
    Set-Content -Path $envAux -Encoding ASCII -Value @(
        "DB_HOST=localhost","DB_PORT=3306","DB_USER=root","DB_PASSWORD=$myPass","DB_NAME=conexion_escolar_aux","SECRET_KEY=$sk","PORT=4000")
    Ok "Cree aux_api\.env (misma SECRET_KEY que el backend)"
} else { Aviso "aux_api\.env ya existe: no lo toque." }

Remove-Item Env:PGPASSWORD, Env:MYSQL_PWD -ErrorAction SilentlyContinue
Paso "Listo"
Write-Host "Bases listas. Ahora sigue la seccion de arranque de la guia local (backend y aux_api)." -ForegroundColor Green
