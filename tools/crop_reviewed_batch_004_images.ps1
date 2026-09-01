param(
    [string]$PagesDir = "tmp/manual_extraction/enunciados_004/pages",
    [string]$OutputDir = "tmp/manual_extraction/enunciados_004/crops"
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

$source = Join-Path $PagesDir "id_1090_q49_pagina_17.png"
Save-Crop $source "q049_1.jpg" 610 380 360 235
Save-Crop $source "q049_alt_A.jpg" 155 665 500 215
Save-Crop $source "q049_alt_B.jpg" 155 855 500 220
Save-Crop $source "q049_alt_C.jpg" 155 1065 500 230
Save-Crop $source "q049_alt_D.jpg" 795 665 500 215
Save-Crop $source "q049_alt_E.jpg" 795 855 500 220

Get-ChildItem $OutputDir | Select-Object Name, Length
