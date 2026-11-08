param([switch]$Clone)

$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $true

$repo = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$runtime = Join-Path (Split-Path $repo -Parent) 'shorts-runtime'
$bootstrap = Join-Path $runtime 'bootstrap'
$uv = Join-Path $bootstrap 'bin/uv.exe'
$python = Join-Path $runtime 'tts-venv/Scripts/python.exe'

if (-not (Test-Path -LiteralPath $uv)) {
    py -3 -m pip install --disable-pip-version-check --target $bootstrap uv
    if ($LASTEXITCODE -ne 0) { throw 'Installing uv failed' }
}

$env:UV_CACHE_DIR = Join-Path $runtime 'uv-cache'
$env:UV_PYTHON_INSTALL_DIR = Join-Path $runtime 'python'
if (-not (Test-Path -LiteralPath $python)) {
    & $uv venv --python 3.12 --managed-python (Join-Path $runtime 'tts-venv')
    if ($LASTEXITCODE -ne 0) { throw 'Creating the Python environment failed' }
}

& $uv pip install --python $python --torch-backend cpu -r (Join-Path $PSScriptRoot 'requirements.txt')
if ($LASTEXITCODE -ne 0) { throw 'Installing Qwen3-TTS dependencies failed' }
& $python (Join-Path $PSScriptRoot 'qwen_narrate.py') --check
if ($LASTEXITCODE -ne 0) { throw 'Loading the Qwen3-TTS model failed' }
if ($Clone) {
    & $python (Join-Path $PSScriptRoot 'qwen_narrate.py') --check-clone
    if ($LASTEXITCODE -ne 0) { throw 'Loading the Qwen3-TTS cloning model failed' }
}
