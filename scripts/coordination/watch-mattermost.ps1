param(
  [string]$ServerUrl = $(if ($env:MATTERMOST_URL) { $env:MATTERMOST_URL } else { "http://8.141.111.33:8065" }),
  [string]$Token = $env:MATTERMOST_TOKEN,
  [string]$Team = $(if ($env:MATTERMOST_TEAM) { $env:MATTERMOST_TEAM } else { "carbonrag" }),
  [string[]]$Channels = @("carbonrag-control", "carbonrag-review"),
  [string[]]$TriggerTypes = @("PLAN", "BLOCK", "REVIEW_READY"),
  [string[]]$IgnoreUsernames = @("t1-director", "t1-codex"),
  [int]$PollSeconds = 15,
  [switch]$Once,
  [switch]$ReplayLatest,
  [switch]$LaunchCodexResume,
  [switch]$LaunchCodexExecReview,
  [string]$Workspace = (Resolve-Path ".").Path,
  [string]$StatePath = "coordination.local.json",
  [string]$TriggerOutDir = "logs/coordination"
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

if (-not $ServerUrl) { throw "MATTERMOST_URL is required, for example http://8.141.111.33:8065" }
if (-not $Token) { throw "MATTERMOST_TOKEN is required" }
if (-not $Team) { $Team = "carbonrag" }

$ServerUrl = $ServerUrl.TrimEnd("/")
$Headers = @{ Authorization = "Bearer $Token" }

function Invoke-MattermostJson {
  param(
    [Parameter(Mandatory = $true)][string]$Uri
  )
  $response = Invoke-WebRequest -Method Get -Uri $Uri -Headers $Headers -UseBasicParsing
  $stream = $response.RawContentStream
  if ($stream.CanSeek) { $stream.Position = 0 }
  $reader = New-Object System.IO.StreamReader($stream, [System.Text.Encoding]::UTF8)
  $text = $reader.ReadToEnd()
  return $text | ConvertFrom-Json
}

function Read-State {
  param([string]$Path)
  if (-not (Test-Path -LiteralPath $Path)) {
    return @{ mattermost_watch = @{ last_create_at = @{} } }
  }
  $raw = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
  if (-not $raw.Trim()) {
    return @{ mattermost_watch = @{ last_create_at = @{} } }
  }
  $obj = $raw | ConvertFrom-Json
  $lastCreateAt = @{}
  if ($obj.mattermost_watch -and $obj.mattermost_watch.last_create_at) {
    foreach ($property in $obj.mattermost_watch.last_create_at.PSObject.Properties) {
      $lastCreateAt[$property.Name] = [long]$property.Value
    }
  }
  return @{ mattermost_watch = @{ last_create_at = $lastCreateAt } }
}

function Write-State {
  param([hashtable]$State, [string]$Path)
  $State | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $Path -Encoding UTF8
}

function Get-ChannelMap {
  $teamInfo = Invoke-MattermostJson -Uri "$ServerUrl/api/v4/teams/name/$Team"
  $me = Invoke-MattermostJson -Uri "$ServerUrl/api/v4/users/me"
  $joined = Invoke-MattermostJson -Uri "$ServerUrl/api/v4/users/$($me.id)/teams/$($teamInfo.id)/channels"
  $map = @{}
  foreach ($name in $Channels) {
    $channel = $joined | Where-Object { $_.name -eq $name } | Select-Object -First 1
    if (-not $channel) {
      Write-Warning "Channel not joined or not found: $name"
      continue
    }
    $map[$name] = $channel.id
  }
  return $map
}

function Get-RecentPosts {
  param([string]$ChannelId)
  $posts = Invoke-MattermostJson -Uri "$ServerUrl/api/v4/channels/$ChannelId/posts?page=0&per_page=30"
  $items = @()
  foreach ($id in $posts.order) {
    $post = $posts.posts.$id
    if ($post.delete_at -ne 0) { continue }
    $items += $post
  }
  return $items | Sort-Object create_at
}

function Get-Username {
  param([string]$UserId)
  $user = Invoke-MattermostJson -Uri "$ServerUrl/api/v4/users/$UserId"
  return $user.username
}

function Get-MessageType {
  param([string]$Message)
  $match = [regex]::Match($Message, "\[(PLAN|ACK|BLOCK|LOCK|UNLOCK|DECISION|CHANGED|REVIEW_READY|ABORT)\]")
  if ($match.Success) { return $match.Groups[1].Value }
  return $null
}

function Invoke-CodexResume {
  param(
    [string]$Prompt,
    [string]$Workspace
  )
  $prompt64 = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($Prompt))
  $workspaceEscaped = $Workspace.Replace("'", "''")
  $command = @"
`$p = [System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('$prompt64'))
codex resume --last -C '$workspaceEscaped' `$p
"@
  Start-Process powershell -ArgumentList @("-NoProfile", "-NoExit", "-Command", $command) | Out-Null
}

function Write-TriggerFile {
  param(
    [string]$ChannelName,
    [string]$Username,
    [string]$Type,
    [string]$Message,
    [long]$CreateAt,
    [string]$OutDir
  )
  $resolvedOutDir = Join-Path $Workspace $OutDir
  New-Item -ItemType Directory -Force -Path $resolvedOutDir | Out-Null
  $time = [DateTimeOffset]::FromUnixTimeMilliseconds($CreateAt).ToOffset([TimeSpan]::FromHours(8))
  $stamp = $time.ToString("yyyyMMdd-HHmmss")
  $fileName = "$stamp-$ChannelName-$Type.md"
  $targetPath = Join-Path $resolvedOutDir $fileName
  $content = @(
    "# Mattermost trigger",
    "",
    "- channel: $ChannelName",
    "- user: $Username",
    "- type: $Type",
    "- time: $($time.ToString("yyyy-MM-dd HH:mm:ss zzz"))",
    "",
    "## Message",
    "",
    "-----",
    $Message,
    "-----",
    "",
    "## Codex handoff prompt",
    "",
    "-----",
    "Read AGENTS.md, OpenSpec, latest Mattermost messages, and related PR state first.",
    "This watcher captured a $Type event from channel $ChannelName, sender $Username.",
    "If this is REVIEW_READY: run read-only PR review, OpenSpec/tests/key diff checks, then suggest approve/request changes/comment.",
    "If this is PLAN/BLOCK: provide #1 coordination advice for ACK/BLOCK/DECISION. Do not edit code automatically.",
    "Do not approve, merge, push, or modify business code unless the user explicitly asks.",
    "-----"
  ) -join [Environment]::NewLine
  $content | Set-Content -LiteralPath $targetPath -Encoding UTF8
  $latestPath = Join-Path $resolvedOutDir "latest-trigger.md"
  $content | Set-Content -LiteralPath $latestPath -Encoding UTF8
  return $targetPath
}

function Invoke-CodexExecReview {
  param(
    [string]$TriggerFile,
    [string]$Workspace
  )
  $resolvedOutDir = Join-Path $Workspace "logs/coordination"
  New-Item -ItemType Directory -Force -Path $resolvedOutDir | Out-Null
  $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
  $outputPath = Join-Path $resolvedOutDir "$stamp-codex-review-output.md"
  $prompt = @(
    "You are doing a read-only review triggered by Mattermost. Do not edit code.",
    "Read AGENTS.md, OpenSpec, the Mattermost trigger file, and related PR state first.",
    "Trigger file: $TriggerFile",
    "",
    "If the trigger type is REVIEW_READY, find the related PR and run read-only review:",
    "1. gh pr view / checkout",
    "2. openspec validate --all",
    "3. target tests or CI status checks",
    "4. key diff risk assessment",
    "5. output approve / comment / request changes recommendation.",
    "",
    "Never approve, merge, push, or modify files automatically."
  ) -join [Environment]::NewLine
  $prompt64 = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($prompt))
  $workspaceEscaped = $Workspace.Replace("'", "''")
  $outputEscaped = $outputPath.Replace("'", "''")
  $command = @"
`$p = [System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('$prompt64'))
codex exec -C '$workspaceEscaped' -o '$outputEscaped' `$p
Write-Host ''
Write-Host 'Codex exec output: $outputEscaped' -ForegroundColor Green
if (Test-Path -LiteralPath '$outputEscaped') { Get-Content -LiteralPath '$outputEscaped' -Encoding UTF8 }
"@
  Start-Process powershell -ArgumentList @("-NoProfile", "-NoExit", "-Command", $command) | Out-Null
  return $outputPath
}

function Handle-Trigger {
  param(
    [string]$ChannelName,
    [string]$Username,
    [string]$Type,
    [string]$Message,
    [long]$CreateAt
  )
  $time = [DateTimeOffset]::FromUnixTimeMilliseconds($CreateAt).ToOffset([TimeSpan]::FromHours(8)).ToString("yyyy-MM-dd HH:mm:ss")
  Write-Host ""
  Write-Host "==> Mattermost trigger detected" -ForegroundColor Yellow
  Write-Host "channel: $ChannelName"
  Write-Host "user:    $Username"
  Write-Host "type:    $Type"
  Write-Host "time:    $time"
  Write-Host "message:"
  Write-Host $Message
  try { [Console]::Beep(880, 180); [Console]::Beep(1175, 180) } catch {}

  $triggerFile = Write-TriggerFile -ChannelName $ChannelName -Username $Username -Type $Type -Message $Message -CreateAt $CreateAt -OutDir $TriggerOutDir
  Write-Host "Trigger file: $triggerFile" -ForegroundColor Cyan

  if ($LaunchCodexResume) {
    $prompt = @(
      "Mattermost coordination trigger detected.",
      "",
      "Channel: $ChannelName",
      "Sender: $Username",
      "Type: $Type",
      "Time: $time",
      "",
      "Original message:",
      $Message,
      "",
      "Read AGENTS.md, latest Mattermost messages, and related PR/OpenSpec state.",
      "If this is REVIEW_READY, enter read-only review flow. If this is PLAN/BLOCK, provide #1 handling advice.",
      "Do not approve, merge, request changes, or modify code unless the user explicitly asks."
    ) -join [Environment]::NewLine
    Invoke-CodexResume -Prompt $prompt -Workspace $Workspace
    Write-Host "Launched: codex resume --last" -ForegroundColor Green
  }

  if ($LaunchCodexExecReview -and $Type -eq "REVIEW_READY") {
    $outputPath = Invoke-CodexExecReview -TriggerFile $triggerFile -Workspace $Workspace
    Write-Host "Launched: codex exec read-only review -> $outputPath" -ForegroundColor Green
  }
}

$channelMap = Get-ChannelMap
if ($channelMap.Count -eq 0) { throw "No watchable Mattermost channels found." }

Write-Host "Watching Mattermost channels: $($channelMap.Keys -join ', ')"
Write-Host "Trigger types: $($TriggerTypes -join ', ')"
Write-Host "Ignored users: $($IgnoreUsernames -join ', ')"
Write-Host "Launch Codex resume: $LaunchCodexResume"
Write-Host "Launch Codex exec review: $LaunchCodexExecReview"
Write-Host "State path: $StatePath"
Write-Host "Trigger out dir: $TriggerOutDir"

while ($true) {
  $state = Read-State -Path $StatePath
  if (-not $state.Contains("mattermost_watch")) { $state["mattermost_watch"] = @{} }
  if (-not $state["mattermost_watch"].Contains("last_create_at")) { $state["mattermost_watch"]["last_create_at"] = @{} }

  foreach ($channelName in $channelMap.Keys) {
    $channelId = $channelMap[$channelName]
    $posts = @(Get-RecentPosts -ChannelId $channelId)
    if ($posts.Count -eq 0) { continue }

    $latestCreateAt = [long](($posts | Sort-Object create_at -Descending | Select-Object -First 1).create_at)
    $hasExistingState = $state["mattermost_watch"]["last_create_at"].Contains($channelName)

    if (-not $hasExistingState -and -not $ReplayLatest) {
      $state["mattermost_watch"]["last_create_at"][$channelName] = $latestCreateAt
      Write-Host "Initialized $channelName at $latestCreateAt"
      continue
    }

    $lastCreateAt = 0
    if ($hasExistingState) { $lastCreateAt = [long]$state["mattermost_watch"]["last_create_at"][$channelName] }

    foreach ($post in ($posts | Where-Object { [long]$_.create_at -gt $lastCreateAt })) {
      $username = Get-Username -UserId $post.user_id
      $type = Get-MessageType -Message $post.message
      if ($type -and ($TriggerTypes -contains $type) -and -not ($IgnoreUsernames -contains $username)) {
        Handle-Trigger -ChannelName $channelName -Username $username -Type $type -Message $post.message -CreateAt ([long]$post.create_at)
      }
    }

    $state["mattermost_watch"]["last_create_at"][$channelName] = $latestCreateAt
  }

  Write-State -State $state -Path $StatePath
  if ($Once) { break }
  Start-Sleep -Seconds $PollSeconds
}
