param(
  [string]$Url = "http://127.0.0.1:8099/",
  [string]$Output = "C:\Users\Public\design-preview.png",
  [int]$Width = 1440,
  [int]$Height = 1400
)

$ChromeCandidates = @(
  "C:\Program Files\Google\Chrome\Application\chrome.exe",
  "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
  "C:\Program Files\Microsoft\Edge\Application\msedge.exe",
  "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
)

$Browser = $ChromeCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $Browser) {
  throw "No Windows Chrome/Edge browser found for headless screenshot."
}

$args = @(
  "--headless=new",
  "--disable-gpu",
  "--hide-scrollbars",
  "--no-first-run",
  "--window-size=$Width,$Height",
  "--screenshot=$Output",
  $Url
)

Start-Process -FilePath $Browser -ArgumentList $args -Wait -NoNewWindow
if (-not (Test-Path $Output)) {
  throw "Screenshot was not created at $Output"
}

$item = Get-Item $Output
Write-Output "screenshot=$($item.FullName) bytes=$($item.Length)"
