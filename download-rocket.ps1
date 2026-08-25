cd C:\Users\Administrator\Downloads\done_yyuyu\rocket-download
python -m http.server 8001http://localhost:8001$site = "https://hello-problem-solver-2.replit.app"
$out = ".\rocket-download"

New-Item -ItemType Directory -Force "$out\assets" | Out-Null

$html = (Invoke-WebRequest -UseBasicParsing "$site/rocket").Content
Set-Content "$out\index.html" $html -Encoding utf8

$queue = [System.Collections.Generic.Queue[string]]::new()
$seen = [System.Collections.Generic.HashSet[string]]::new()

[regex]::Matches($html, '(?:src|href)="([^"]+)"') |
    ForEach-Object {
        $path = $_.Groups[1].Value -replace '\?.*$', ''
        if ($path.StartsWith("/assets/") -or $path -eq "/rocket-static.png") {
            $queue.Enqueue($path)
        }
    }

while ($queue.Count -gt 0) {
    $path = $queue.Dequeue()

    if (-not $seen.Add($path)) {
        continue
    }

    $relativePath = $path.TrimStart("/")
    $destination = Join-Path $out ($relativePath -replace "/", "\")
    $directory = Split-Path $destination

    New-Item -ItemType Directory -Force $directory | Out-Null

    try {
        Invoke-WebRequest `
            -UseBasicParsing `
            -Uri "$site$path" `
            -OutFile $destination

        if ($destination.EndsWith(".js")) {
            $js = Get-Content -Raw $destination

            [regex]::Matches($js, '(?:from|import\()["''](\./[^"'']+)["'']') |
                ForEach-Object {
                    $dependency = $_.Groups[1].Value
                    $dependencyPath = "/" + (($path -replace "/[^/]+$", "") + "/" + $dependency.TrimStart("./")) -replace "/+", "/"

                    if (-not $seen.Contains($dependencyPath)) {
                        $queue.Enqueue($dependencyPath)
                    }
                }
        }
    }
    catch {
        Write-Warning "Failed: $path"
    }
}

Get-ChildItem $out -Recurse
