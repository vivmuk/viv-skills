---
name: wsl-disk-management
version: 1
description: "Diagnose and reclaim disk space on the Windows C: drive from within WSL. Covers identifying space hogs across the Windows/WSL boundary, cleaning caches, compacting the WSL vhdx, and moving data to OneDrive."
triggers:
  - disk space
  - low disk
  - C: drive full
  - free up space
  - clean up disk
  - WSL disk
  - vhdx compact
  - out of space
  - storage cleanup
---

# WSL Disk Space Management

When the Windows C: drive fills up and you're working from WSL, you need to measure, clean, and compact across the Windows/WSL boundary. The WSL virtual disk (vhdx) on C: never shrinks automatically — deleting files inside WSL only frees C: space after compaction.

## Diagnosis

### Check C: drive free space and available backup destinations first
```bash
df -h /mnt/c /mnt/d /mnt/e /mnt/f 2>/dev/null
ls -la /mnt/ | grep -E '^d' | awk '{print $NF}'
```

**Before promising to back up to OneDrive or an "E drive", verify they actually exist and have free space.** In this session the user asked to back up to OneDrive and E:, but only C: (nearly full) and a tiny D: existed. The real space hog turned out to be the WSL virtual disk itself, which cannot safely live on OneDrive and had no other local destination.

### Check C: drive free space
```bash
df -h /mnt/c/
```

### Measure Windows-side folder sizes (USE PowerShell, NOT du)

**⚠️ `du` through `/mnt/c/` is EXTREMELY slow** and often times out for large directories (AppData, Program Files). Always use PowerShell for Windows-side measurement.

```bash
powershell.exe -NoProfile -File - <<'PSEOF'
Get-ChildItem -Path 'C:\Users\vivek\AppData\Local' -Directory -ErrorAction SilentlyContinue | ForEach-Object {
    $size = (Get-ChildItem -Path $_.FullName -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
    [PSCustomObject]@{Name=$_.Name; SizeGB=[math]::Round($size/1GB,2)}
} | Sort-Object SizeGB -Descending | Select-Object -First 25 | Format-Table -AutoSize
PSEOF
```

Key PowerShell invocation patterns from WSL:
- **`powershell.exe -NoProfile -File -`** with a heredoc — avoids bash escaping issues with `$` signs
- **`powershell.exe -NoProfile -Command "..."`** — for short one-liners, but `$` in the command gets eaten by bash; escape with `\$` or use the heredoc approach above

### Measure WSL-side usage
```bash
du -sh /home/<user>/* /home/<user>/.* 2>/dev/null | sort -rh | head -30
df -h /
```

### Common space hogs by location

| Location | Typical Size | Safe to Clean? |
|----------|-------------|-----------------|
| `AppData/Local/wsl/` (vhdx) | 20-50 GB | Compact only (don't delete). This single file often dominates C: usage. |
| `AppData/Local/npm-cache/` | 2-10 GB | Yes — `npm cache clean --force` |
| `AppData/Local/pnpm/` | 0.5-2 GB | Yes — `pnpm store prune` |
| `AppData/Local/ms-playwright/` | 0.5-1 GB | Yes — `rm -rf` if not needed |
| `AppData/Local/pip/` | 0.1-0.5 GB | Yes — `pip cache purge` |
| `AppData/Roaming/Telegram Desktop/` | 0.5-2 GB | Partial — clear cache in Telegram settings |
| `AppData/Roaming/npm/` | 0.3-1 GB | Yes — `npm cache clean --force` |
| `~/.npm/_cacache` (WSL) | 2-8 GB | Yes — `npm cache clean --force` |
| `~/.npm/_npx` (WSL) | 0.5-2 GB | Yes — `rm -rf ~/.npm/_npx` |
| `~/.cache/uv` (WSL) | 1-3 GB | Yes — `uv cache clean` |
| `~/.cache/camoufox` (WSL) | 1-2 GB | Yes — `rm -rf ~/.cache/camoufox` |
| `~/.cache/ms-playwright` (WSL) | 0.5-1 GB | Yes — `rm -rf ~/.cache/ms-playwright` |
| `~/.local/share/pnpm` (WSL) | 1-3 GB | Partial — `pnpm store prune` from home dir |
| `C:\pagefile.sys` | 2-8 GB | Reduce via System Properties if RAM is sufficient |
| `C:\hiberfil.sys` | 2-8 GB | Disable hibernation if not used: `powershell.exe -Command "powercfg /hibernate off"` |

## Cleaning Caches

### Windows-side caches
```bash
# npm cache (biggest win)
cmd.exe /c "rd /s /q C:\Users\vivek\AppData\Local\npm-cache\_cacache"

# pnpm cache
cmd.exe /c "rd /s /q C:\Users\vivek\AppData\Local\pnpm"

# Playwright browsers
cmd.exe /c "rd /s /q C:\Users\vivek\AppData\Local\ms-playwright"

# pip cache
cmd.exe /c "rd /s /q C:\Users\vivek\AppData\Local\pip"
```

**Use `cmd.exe /c "rd /s /q ..."`** for deleting Windows directories from WSL — it's faster and more reliable than `rm -rf` through `/mnt/c/`.

### WSL-side caches
```bash
cd /home/<user>  # IMPORTANT: change dir first to avoid cwd issues

npm cache clean --force
uv cache clean
pip cache purge
rm -rf ~/.cache/camoufox
rm -rf ~/.cache/ms-playwright
rm -rf ~/.cache/electron
rm -rf ~/.npm/_npx
```

**⚠️ Always `cd /home/<user>` before running pnpm/npm commands.** If your cwd is `/mnt/c/WINDOWS/system32` (default for WSL sessions), pnpm/npm try to write temp files there and fail with EACCES.

### pnpm store pruning
```bash
cd /home/<user>
pnpm store prune
```
Note: `pnpm store prune` only removes packages not referenced by any project. If all packages are still linked, it removes nothing. The store at `~/.local/share/pnpm` can be 2-3 GB.

## Compacting the WSL Virtual Disk (BIGGEST WIN)

**This is the most important step.** Deleting files inside WSL frees space logically but the vhdx file on C: never shrinks until compacted. A 35 GB vhdx with only 22 GB used wastes 13 GB on C:.

### Step 1: Clean up inside WSL first
Run all the cache cleaning steps above, delete unused projects, etc.

### Step 2: Create the compaction script on Windows
```bash
cat > /mnt/c/Users/<winuser>/compact_wsl.ps1 << 'PSEOF'
Write-Host "Shutting down WSL..."
wsl --shutdown
Start-Sleep -Seconds 5

Write-Host "Compacting WSL virtual disk..."
$vhdxPath = "C:\Users\<winuser>\AppData\Local\wsl\{<guid>}\ext4.vhdx"
$sizeBefore = (Get-Item $vhdxPath).Length / 1GB
Write-Host "Before: $([math]::Round($sizeBefore, 2)) GB"

$diskpartScript = @"
select vdisk file="$vhdxPath"
attach vdisk readonly
compact vdisk
detach vdisk
exit
"@

$diskpartScript | diskpart

$sizeAfter = (Get-Item $vhdxPath).Length / 1GB
Write-Host "After: $([math]::Round($sizeAfter, 2)) GB"
Write-Host "Saved: $([math]::Round($sizeBefore - $sizeAfter, 2)) GB"

Remove-Item "C:\Users\<winuser>\compact_wsl.ps1" -Force
PSEOF
```

To find your vhdx path:
```bash
powershell.exe -NoProfile -Command "Get-ChildItem -Path 'C:\Users\<winuser>\AppData\Local\wsl' -Recurse -Filter '*.vhdx' | Select-Object FullName, @{N='SizeGB';E={[math]::Round(\$_.Length/1GB,2)}}"
```

### Step 3: Run from PowerShell as Administrator
Open PowerShell as Administrator (right-click Start -> Terminal Admin), then:
```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force; & "C:\Users\<winuser>\compact_wsl.ps1"
```

**This kills your WSL session** — save all work first.

### Alternative: Hyper-V Optimize-VHD
If Hyper-V is enabled, this is simpler:
```powershell
Optimize-VHD -Path "C:\Users\<winuser>\AppData\Local\wsl\{<guid>}\ext4.vhdx" -Mode Full
```

## When the User Asks to Back Up/Move Files

Users often frame disk cleanup as "back up to OneDrive, then move the rest to E:". Treat this as a disk-space triage request, not a literal copy operation.

### Verify before acting
1. Does OneDrive actually exist and have room? Check `/mnt/c/Users/<user>/OneDrive` and OneDrive's own cloud quota — don't assume it can absorb tens of gigabytes.
2. Does the requested drive (E:, etc.) exist and have enough free space? `df -h /mnt/e` may show nothing if the drive isn't mounted or doesn't exist.
3. Is the bulk of the usage a **single WSL vhdx**? If so, copying it elsewhere is usually the wrong answer — compact it instead.

### What's safe for OneDrive
- Normal project directories, documents, photos, videos.
- **NOT** live WSL `ext4.vhdx` files, virtual machine disks, databases in use, or any file locked by another process.

### When there's no other drive
If the only mounted drives are C: (full) and a tiny D:, the practical options are:
1. Clean caches inside WSL and Windows.
2. Delete or move non-essential files to cloud storage.
3. Compact the WSL vhdx.
4. Add external storage (USB, SD card, network share) — don't invent an E: drive.

## Moving Projects to OneDrive or External Storage

Moving WSL project folders to OneDrive saves C: space, but **cross-filesystem copies are extremely slow** — rsync/cp from `/home/` to `/mnt/c/Users/.../OneDrive/` can timeout on folders over ~500 MB.

### Critical: verify the copy before deleting the source

Cross-filesystem copies to OneDrive, network drives, or removable media (SD cards, USB sticks) can silently succeed at the tool level while leaving incomplete or empty directory trees. The destination may report the expected size during the copy, then drop data on timeout or flush failure. **Always verify byte counts or file counts before removing the original.**

```bash
# 1. Copy (do NOT delete source yet)
rsync -aH --delete /home/<user>/<project>/ /mnt/<dest>/<project>/

# 2. Verify file count and total bytes match
find /home/<user>/<project> -type f | wc -l
find /mnt/<dest>/<project> -type f | wc -l
du -sb /home/<user>/<project>
du -sb /mnt/<dest>/<project>

# 3. Spot-check actual file contents
cat /mnt/<dest>/<project>/README.md >/dev/null

# 4. Only then remove source and replace with symlink
rm -rf /home/<user>/<project>
ln -s /mnt/<dest>/<project> /home/<user>/<project>
```

**Never rely on `ls -la` or directory listings alone** — a failed copy can leave a perfect-looking tree of empty directories.

### Recommended approach: Move from Windows Explorer
1. Open Windows Explorer
2. Navigate to `\\wsl$\<distro>\home\<user>\`
3. Cut the project folder
4. Paste into `C:\Users\<winuser>\OneDrive\WSL-Projects\`

### Create symlinks after moving
```bash
# From WSL
ln -s /mnt/c/Users/<winuser>/OneDrive/WSL-Projects/<project> /home/<user>/<project>
```

### If you must move from WSL (small folders only)
```bash
# For folders < 200 MB, rsync works
mkdir -p /mnt/c/Users/<winuser>/OneDrive/WSL-Projects/
rsync -a /home/<user>/<project>/ /mnt/c/Users/<winuser>/OneDrive/WSL-Projects/<project>/
rm -rf /home/<user>/<project>
ln -s /mnt/c/Users/<winuser>/OneDrive/WSL-Projects/<project> /home/<user>/<project>
```

### The most reliable method: robocopy from Windows across `\\wsl$\`

When `rsync`/`cp` through a WSL `drvfs` mount silently drops file data (common with removable media, OneDrive, and SD cards), use Windows `robocopy` from the Windows side. This reads from `\\wsl$\<distro>\home\<user>\...` and writes to the destination with native Windows I/O.

```bash
# Copy a WSL directory to an external drive E:
powershell.exe -NoProfile -Command "robocopy '\\\\wsl$\\Ubuntu\\home\\vivgates\\.npm' 'E:\Backups\WSL_Cache\npm' /MIR /NP /NDL /NFL /R:1 /W:1 /XJD /XJF"
```

Robocopy options used:
- `/MIR` — mirror source to destination (same as rsync --delete)
- `/NP` `/NDL` `/NFL` — suppress progress spam and directory/file listings
- `/R:1 /W:1` — only retry once, wait 1 second (default is 1 million retries)
- `/XJD /XJF` — skip junction points and symlinks (avoids broken `.bin` stubs in npm `_npx`)

After robocopy, verify from Windows before deleting the source:
```bash
powershell.exe -NoProfile -Command "
  $srcFiles = (Get-ChildItem '\\\\wsl$\\Ubuntu\\home\\vivgates\\.npm' -Recurse -File -ErrorAction SilentlyContinue | Measure-Object).Count
  $dstFiles = (Get-ChildItem 'E:\Backups\WSL_Cache\npm' -Recurse -File -ErrorAction SilentlyContinue | Measure-Object).Count
  $srcBytes = (Get-ChildItem '\\\\wsl$\\Ubuntu\\home\\vivgates\\.npm' -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
  $dstBytes = (Get-ChildItem 'E:\Backups\WSL_Cache\npm' -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
  Write-Host \"src: `$srcFiles files, `$([math]::Round(\$srcBytes/1GB,2)) GB\"
  Write-Host \"dst: `$dstFiles files, `$([math]::Round(\$dstBytes/1GB,2)) GB\"
"
```

Only after counts/bytes match, remove the source and replace with a symlink:
```bash
rm -rf /home/vivgates/.npm
ln -s /mnt/e/Backups/WSL_Cache/npm /home/vivgates/.npm
```

See `references/wsl-drvfs-silent-file-drop-robocopy-workaround.md` for the full reproduction recipe from a session where the `drvfs` path to an SD card copied only directory skeletons.

## Pitfalls

- **Don't promise to back up to OneDrive or E: before checking they exist and have space.** OneDrive may be present but full; E: may not be mounted at all.
- **`du` through `/mnt/c/` times out** for large directories. Always use PowerShell for Windows-side measurement.
- **Deleting files in WSL doesn't free C: space** until the vhdx is compacted. Always run compaction after cleanup.
- **Never rely on `ls -la` or directory listings to verify a cross-filesystem copy.** Empty directories can look identical to complete trees. Verify file counts and total bytes (`find ... -type f | wc -l` and `du -sb`) and spot-read a file before deleting the source.
- **Moving to removable media (SD card, USB) is even riskier than OneDrive.** SD cards are slow, can be FAT/exFAT with file-size or permission limits, and 9p/DrvFS transfers can silently truncate. Treat every removable copy as suspect until verified. See `references/wsl-drvfs-silent-file-drop-robocopy-workaround.md` for the robocopy workaround.
- **WSL `drvfs` mounts to removable drives can silently drop file contents.** The destination directory tree may look complete while files are empty or missing. Use Windows `robocopy` over `\\wsl$\` instead of `rsync`/`cp` through `/mnt/e/` for large moves to SD cards or USB sticks.
- **Cross-filesystem copies are 10-50x slower** than same-filesystem. Moving 1 GB from WSL ext4 to /mnt/c/ can take minutes.
- **WSL default cwd** is often `/mnt/c/WINDOWS/system32`. Always `cd /home/<user>` before running npm/pnpm to avoid EACCES errors.
- **`rm -rf` through `/mnt/c/`** can be slow and may require user approval in some tool setups. Use `cmd.exe /c "rd /s /q ..."` instead.
- **pnpm store prune removes nothing** if all packages are still referenced by projects. Only removes orphaned packages.
- **OneDrive sync** — files moved to OneDrive will sync to the cloud, which is good for backup but means the local OneDrive cache still uses C: space unless "Files On-Demand" is enabled (cloud-only placeholders use ~0 local space).

## Quick Cleanup Checklist

When the user says "free up space" or "C: drive is full":

1. `df -h /mnt/c/` — check current free space
2. PowerShell scan of `AppData/Local` — identify big folders
3. Clean Windows caches: npm, pnpm, pip, playwright (use `cmd.exe /c "rd /s /q ..."`)
4. Clean WSL caches: `npm cache clean --force`, `uv cache clean`, `pip cache purge`, `rm -rf ~/.cache/camoufox ~/.cache/ms-playwright ~/.npm/_npx`
5. Delete unused project folders inside WSL (or move them after verified copy)
6. If moving to OneDrive/external storage, see the verification rule in "Moving Projects to OneDrive or External Storage" below
7. Create and run the vhdx compaction script (requires PowerShell Admin + kills WSL)
8. `df -h /mnt/c/` — verify freed space
