param(
    [string]$Batch005PagesDir = "output/quality_batches/_inspect_005/pages",
    [string]$OutputDir = "tmp/manual_extraction/batches_005_007/crops"
)

Add-Type -AssemblyName System.Drawing
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

function Save-Crop([string]$Source, [string]$Name, [int]$X, [int]$Y, [int]$Width, [int]$Height) {
    $image = [System.Drawing.Bitmap]::FromFile($Source)
    try {
        $rectangle = [System.Drawing.Rectangle]::new($X, $Y, $Width, $Height)
        $crop = $image.Clone($rectangle, $image.PixelFormat)
        try {
            $crop.Save((Join-Path $OutputDir $Name), [System.Drawing.Imaging.ImageFormat]::Jpeg)
        } finally {
            $crop.Dispose()
        }
    } finally {
        $image.Dispose()
    }
}

# Q86: onda estacionaria e marcadores I-V, sem o texto e as alternativas.
Save-Crop (Join-Path $Batch005PagesDir "id_1127_q86_pagina_30.png") "q086_1.jpg" 435 1370 720 300

# Q114: equacao com as quatro formulas estruturais e o catalisador.
Save-Crop (Join-Path $Batch005PagesDir "id_1335_q114_pagina_9.png") "q114_1.jpg" 330 380 980 225

Get-ChildItem $OutputDir | Select-Object Name, Length
