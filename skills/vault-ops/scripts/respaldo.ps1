# Respaldo del segundo cerebro a un disco FÍSICO DISTINTO.
#
# Por qué existe: el Vault vive en F: (Jeanne) sin sincronización de ningún tipo.
# Su propio protocolo lo declara desde el 2026-07-26 —"Sin sincronización no hay
# respaldo. Un fallo de F: se lleva todo"— y siguió siendo cierto durante días.
# Toda la disciplina del sistema protege contra la incoherencia y nada protegía
# contra la pérdida.
#
# Destino: G: (Perseus), disco físico separado. Un respaldo en el mismo disco no
# es un respaldo: es una copia que muere con el original.
#
# Uso:
#   powershell -ExecutionPolicy Bypass -File respaldo.ps1
#   powershell ... -File respaldo.ps1 -Destino 'D:\BACKUP'   # otro disco
#   powershell ... -File respaldo.ps1 -Verificar             # solo comprobar
#
# `robocopy /MIR` espeja: lo borrado en origen se borra en destino. Eso es lo
# correcto para un espejo, y por eso el historial NO se confía a él sino al
# repositorio git del Vault: si algo se borra por error, git lo recupera aunque
# el espejo ya lo haya replicado. Las dos capas cubren fallos distintos —el
# espejo cubre la muerte del disco, git cubre la del dedo.

param(
    [string]$Origen   = 'F:\OBSIDIAN',
    [string]$Skills   = 'F:\skills\_personales',
    [string]$Repos    = 'F:\REPOSITORIOS\espejos',
    [string]$Destino  = 'G:\BACKUP_SEGUNDO_CEREBRO',
    [switch]$Verificar
)

$ErrorActionPreference = 'Stop'
$sello = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'

function Fallar($msg) { Write-Host "FALLO: $msg" -ForegroundColor Red; exit 1 }

# --- Contrato: sin destino en OTRO disco, no hay respaldo que valga ---
$discoOrigen  = (Split-Path -Qualifier $Origen)
$discoDestino = (Split-Path -Qualifier $Destino)
if ($discoOrigen -eq $discoDestino) {
    Fallar "origen y destino en el mismo disco ($discoOrigen). Un respaldo ahí no protege de nada."
}
if (-not (Test-Path -LiteralPath "$discoDestino\")) {
    Fallar "el disco destino $discoDestino no está disponible."
}
if (-not (Test-Path -LiteralPath $Origen)) { Fallar "no existe el origen $Origen" }

if ($Verificar) {
    Write-Host "=== Verificación de respaldo — $sello ==="
    foreach ($par in @(@{n='vault';d="$Destino\OBSIDIAN";o=$Origen},
                       @{n='skills';d="$Destino\skills_personales";o=$Skills})) {
        if (-not (Test-Path -LiteralPath $par.d)) { Write-Host "  $($par.n): SIN RESPALDO" -ForegroundColor Red; continue }
        $no = (Get-ChildItem -LiteralPath $par.o -Recurse -Force -File -ErrorAction SilentlyContinue).Count
        $nd = (Get-ChildItem -LiteralPath $par.d -Recurse -Force -File -ErrorAction SilentlyContinue).Count
        $edad = [math]::Round(((Get-Date) - (Get-Item -LiteralPath $par.d).LastWriteTime).TotalHours, 1)
        $color = if ($nd -ge $no * 0.95) { 'Green' } else { 'Red' }
        Write-Host ("  {0}: origen {1} archivos / respaldo {2} — última escritura hace {3} h" -f $par.n,$no,$nd,$edad) -ForegroundColor $color
    }
    exit 0
}

New-Item -ItemType Directory -Force -Path $Destino | Out-Null

# _PRIVADO se excluye: la regla 2·bis del protocolo del Vault prohíbe incluirlo
# en cualquier respaldo NO CIFRADO, y este espejo lo es. Necesita su propia copia
# cifrada aparte; no se resuelve aquí y el certificado lo declara como hueco.
# .git SÍ se espeja: es la capa de historial, y una historia que muere con el
# disco no es historial. Solo pesa ~700 KB.
$excluirDir = @('_PRIVADO', '.stfolder', '__pycache__', '.venv', 'node_modules')

Write-Host "=== Respaldo del segundo cerebro — $sello ==="
Write-Host "    $Origen  ->  $Destino\OBSIDIAN"

$rcArgs = @("$Origen", "$Destino\OBSIDIAN", '/MIR', '/R:2', '/W:2', '/NFL', '/NDL', '/NP', '/XJ')
$rcArgs += '/XD'; $rcArgs += $excluirDir
robocopy @rcArgs | Out-Null
$rcVault = $LASTEXITCODE

Write-Host "    $Skills  ->  $Destino\skills_personales"
robocopy "$Skills" "$Destino\skills_personales" /MIR /R:2 /W:2 /NFL /NDL /NP /XJ /XD '__pycache__' | Out-Null
$rcSkills = $LASTEXITCODE

# Espejos de los repos de trabajo (~1,1 GB). Hueco detectado el 2026-08-01: el
# historial de git de element, principia, hamcao, shewanella, ecoli, agroglim y
# fenix vivía solo en F:. Un fallo de ese disco se llevaba el vault Y el código.
# Los espejos son `bare`, así que esto respalda historial completo, no una copia
# de trabajo.
#
# ⚠️ NO incluye F:\REPOSITORIOS\sapyria (53 GB de datos clínicos): no cabe con
# holgura en G: y su respaldo es una decisión del usuario, no un automatismo.
# Mientras tanto ese directorio NO tiene copia fuera de F:.
$rcRepos = 0
if (Test-Path -LiteralPath $Repos) {
    Write-Host "    $Repos  ->  $Destino\repos_espejos"
    robocopy "$Repos" "$Destino\repos_espejos" /MIR /R:2 /W:2 /NFL /NDL /NP /XJ | Out-Null
    $rcRepos = $LASTEXITCODE
}

# robocopy: 0-7 = éxito (0 sin cambios, 1 copiados, 2 extras, 3 ambos...). >=8 = error real.
if ($rcVault -ge 8)  { Fallar "robocopy vault devolvió $rcVault" }
if ($rcSkills -ge 8) { Fallar "robocopy skills devolvió $rcSkills" }
if ($rcRepos -ge 8)  { Fallar "robocopy espejos devolvió $rcRepos" }

$n = (Get-ChildItem -LiteralPath "$Destino\OBSIDIAN" -Recurse -Force -File).Count
$mb = [math]::Round(((Get-ChildItem -LiteralPath $Destino -Recurse -Force -File | Measure-Object Length -Sum).Sum)/1MB, 1)
"Último respaldo: $sello`nArchivos del vault: $n`nTamaño total: $mb MB`nOrigen: $Origen`nExcluido: _PRIVADO (respaldo no cifrado, regla 2-bis)" |
    Set-Content -LiteralPath "$Destino\ULTIMO_RESPALDO.txt" -Encoding UTF8

Write-Host "OK — $n archivos del vault, $mb MB en total." -ForegroundColor Green
Write-Host "    Sello en $Destino\ULTIMO_RESPALDO.txt"
