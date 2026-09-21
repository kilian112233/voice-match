param(
    [string]$RepoPath = ".",
    [switch]$Private,
    [string]$Message,
    [string]$Remote = "origin"
)

$ErrorActionPreference = "Stop"
$user = "kilian112233"
$email = "$user@users.noreply.github.com"

$repo = (Resolve-Path $RepoPath).Path
Set-Location $repo

if (-not (Test-Path ".git")) { Write-Error "not a git repo: $repo"; exit 1 }

git config user.name "$user" | Out-Null
git config user.email "$email" | Out-Null

$name = Split-Path $repo -Leaf
$url = "https://github.com/$user/$name.git"
if ((git remote get-url $Remote 2>$null) -ne $url) {
    if (git remote get-url $Remote 2>$null) { git remote set-url $Remote $url }
    else { git remote add $Remote $url }
}

$cred = "protocol=https`nhost=github.com`n" | git credential fill
$token = ($cred | Select-String '^password=').ToString().Substring(9).Trim()
if (-not $token) { Write-Error "git credential fill returned no token"; exit 1 }

$headers = @{ Authorization = "Bearer $token"; 'User-Agent' = 'opencode'; Accept = 'application/vnd.github+json' }

if (-not $Message) {
    if (git status --porcelain | Select-Object -First 1) {
        $untracked = (git status --porcelain | Where-Object { $_ -match '^\?\?' }).Count
        $changed = (git status --porcelain | Where-Object { $_ -notmatch '^\?\?' }).Count
        $Message = "chore: sync ($changed modified, $untracked untracked)"
    } else {
        $Message = "chore: sync"
    }
}

if (git status --porcelain | Select-Object -First 1) {
    git add -A
    git commit -m $Message
}

$branch = git branch --show-current
$vis = if ($Private) { 'true' } else { 'false' }
try {
    Invoke-RestMethod -Method Get -Uri "https://api.github.com/repos/$user/$name" -Headers $headers -ErrorAction Stop | Out-Null
    Write-Output "existing repo: $user/$name"
} catch {
    $body = @{ name = $name; private = ($Private -eq $true); auto_init = $false } | ConvertTo-Json
    $null = Invoke-RestMethod -Method Post -Uri "https://api.github.com/user/repos" -Headers $headers -ContentType 'application/json' -Body $body
    Write-Output "created repo: $user/$name (private=$vis)"
}

$env:GIT_TERMINAL_PROMPT = "0"
git push -u $Remote $branch 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) { Write-Error "push failed"; exit 1 }
Write-Output "pushed branch '$branch' -> https://github.com/$user/$name (private=$vis)"