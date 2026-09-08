param(
    [string]$Batch011PagesDir = "output/quality_batches/_inspect_011/pages",
    [string]$OutputDir = "tmp/manual_extraction/batches_011_012/crops"
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

$q161 = Join-Path $Batch011PagesDir "id_2618_q161_pagina_23.png"
Save-Crop $q161 "q161_alt_A.jpg" 185 835 465 340
Save-Crop $q161 "q161_alt_B.jpg" 185 1180 465 340
Save-Crop $q161 "q161_alt_C.jpg" 185 1525 465 340
Save-Crop $q161 "q161_alt_D.jpg" 835 835 465 340
Save-Crop $q161 "q161_alt_E.jpg" 835 1180 465 340

$q168 = Join-Path $Batch011PagesDir "id_2625_q168_pagina_26.png"
Save-Crop $q168 "q168_alt_A.jpg" 170 555 590 360
Save-Crop $q168 "q168_alt_B.jpg" 170 1005 590 360
Save-Crop $q168 "q168_alt_C.jpg" 170 1455 590 360
Save-Crop $q168 "q168_alt_D.jpg" 820 555 590 360
Save-Crop $q168 "q168_alt_E.jpg" 820 1005 590 360

Get-ChildItem $OutputDir | Select-Object Name, Length
