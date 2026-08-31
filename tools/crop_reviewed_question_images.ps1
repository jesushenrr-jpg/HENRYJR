param(
    [string]$PagesDir = "tmp/manual_extraction/enunciados_002/pages",
    [string]$OutputDir = "tmp/manual_extraction/enunciados_002/crops"
)

Add-Type -AssemblyName System.Drawing
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

function Save-Crop([string]$Source, [string]$Name, [int]$X, [int]$Y, [int]$Width, [int]$Height) {
    $image = [System.Drawing.Bitmap]::FromFile($Source)
    try {
        $rectangle = [System.Drawing.Rectangle]::new($X, $Y, $Width, $Height)
        $crop = $image.Clone($rectangle, $image.PixelFormat)
        try {
            $target = Join-Path $OutputDir $Name
            $crop.Save($target, [System.Drawing.Imaging.ImageFormat]::Jpeg)
        } finally {
            $crop.Dispose()
        }
    } finally {
        $image.Dispose()
    }
}

$q60 = Join-Path $PagesDir "id_381_q60_pagina_21.png"
Save-Crop $q60 "q060_alt_A.jpg" 125 480 620 390
Save-Crop $q60 "q060_alt_D.jpg" 785 480 620 390
Save-Crop $q60 "q060_alt_B.jpg" 125 880 620 390
Save-Crop $q60 "q060_alt_E.jpg" 785 880 620 390
Save-Crop $q60 "q060_alt_C.jpg" 125 1280 620 600

Save-Crop (Join-Path $PagesDir "id_470_q149_pagina_23.png") "q149_1.jpg" 880 1065 520 470
Save-Crop (Join-Path $PagesDir "id_637_q136_pagina_19.png") "q136_1.jpg" 165 435 610 405

Get-ChildItem $OutputDir | Select-Object Name, Length
