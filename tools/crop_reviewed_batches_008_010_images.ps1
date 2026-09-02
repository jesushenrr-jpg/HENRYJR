param(
    [string]$Batch008PagesDir = "output/quality_batches/_inspect_008/pages",
    [string]$Batch009PagesDir = "output/quality_batches/_inspect_009/pages",
    [string]$OutputDir = "tmp/manual_extraction/batches_008_010/crops"
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

Save-Crop (Join-Path $Batch008PagesDir "id_1604_q23_pagina_12.png") "q023_1.jpg" 70 1015 610 430
Save-Crop (Join-Path $Batch008PagesDir "id_1640_q59_pagina_24.png") "q059_1.jpg" 325 225 700 690

$q163 = Join-Path $Batch009PagesDir "id_1744_q163_pagina_25.png"
Save-Crop $q163 "q163_alt_A.jpg" 155 565 325 350
Save-Crop $q163 "q163_alt_B.jpg" 155 975 325 350
Save-Crop $q163 "q163_alt_C.jpg" 155 1380 325 350
Save-Crop $q163 "q163_alt_D.jpg" 740 565 325 350
Save-Crop $q163 "q163_alt_E.jpg" 740 975 325 350

Save-Crop (Join-Path $Batch009PagesDir "id_1783_q22_pagina_11.png") "q022_1.jpg" 715 960 545 470
Save-Crop (Join-Path $Batch009PagesDir "id_1787_q26_pagina_12.png") "q026_1.jpg" 785 1010 445 245

$q118 = Join-Path $Batch009PagesDir "id_2215_q118_pagina_11.png"
Save-Crop $q118 "q118_1.jpg" 400 320 580 280
Save-Crop $q118 "q118_alt_A.jpg" 115 680 430 300
Save-Crop $q118 "q118_alt_B.jpg" 115 1040 430 300
Save-Crop $q118 "q118_alt_C.jpg" 115 1410 430 300
Save-Crop $q118 "q118_alt_D.jpg" 725 680 430 300
Save-Crop $q118 "q118_alt_E.jpg" 725 1040 430 300

Get-ChildItem $OutputDir | Select-Object Name, Length
