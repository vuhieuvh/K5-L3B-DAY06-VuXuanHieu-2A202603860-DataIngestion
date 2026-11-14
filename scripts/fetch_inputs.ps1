$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)
$manifest = Get-Content -Raw -Encoding UTF8 data/manifest.json | ConvertFrom-Json
$revision = '614241f622f53c4eeff9890bdc4f31cfecc418b3'
New-Item -ItemType Directory -Force .local/e5/onnx | Out-Null

function Get-InputFile($url, $destination) {
    curl.exe -fsSL --retry 2 --max-time 240 $url -o "$destination.part"
    if ($LASTEXITCODE -ne 0) { throw "Download failed for $url" }
    Move-Item -Force -LiteralPath "$destination.part" -Destination $destination
}

Get-InputFile $manifest.source_path_or_url '.local/3626-text.pdf'
if ((Get-FileHash -Algorithm SHA256 .local/3626-text.pdf).Hash -ne $manifest.sha256) {
    throw 'PDF checksum differs from the manifest'
}
$files = @('onnx/model_qint8_avx512_vnni.onnx','config.json','tokenizer.json',
    'tokenizer_config.json','special_tokens_map.json')
foreach ($file in $files) {
    Get-InputFile "https://huggingface.co/intfloat/multilingual-e5-small/resolve/$revision/$file" ".local/e5/$file"
}
Set-Content -Encoding ASCII -LiteralPath .local/e5/revision.txt -Value $revision

