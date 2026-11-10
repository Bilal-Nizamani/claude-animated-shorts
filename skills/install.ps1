# Copy the narrated-video skills and their shared tools into %USERPROFILE%\.claude\skills (Windows).
$dest = if ($env:CLAUDE_SKILLS_DIR) { $env:CLAUDE_SKILLS_DIR } else { Join-Path $env:USERPROFILE '.claude\skills' }
New-Item -ItemType Directory -Force $dest | Out-Null
foreach ($d in '_shared', 'short-form-narrative', 'long-form-narrative') {
    $target = Join-Path $dest $d
    if (Test-Path $target) { Remove-Item $target -Recurse -Force }
    Copy-Item (Join-Path $PSScriptRoot $d) $target -Recurse
}
"Installed short-form-narrative, long-form-narrative and _shared into $dest"
