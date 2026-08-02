# Workaround: WSL drvfs silently drops file contents on removable drives

## Symptom

Copying a large WSL directory to an SD card / USB drive / OneDrive via `/mnt/<drive>` (WSL 9p/DrvFS) reports success, and the destination directory tree looks correct, but many or all files are empty or missing.

Specific example from a session:
- Source: `/home/vivgates/.openclaw/workspace` (~8.2 GB)
- Destination: `/mnt/e/Backups/OpenClaw/workspace` on a 30 GB SD card labeled VEGA
- Tool: `rsync -aH --delete` inside `execute_code`
- Result after timeout/rename/delete/symlink:
  - Destination had the full directory skeleton.
  - `find /mnt/e/Backups/OpenClaw/workspace -type f | wc -l` returned **0**.
  - Source was already deleted.

The SD card itself was healthy: writing a 100 MB test file from Windows (`E:\Backups\test-write\test_1gb.bin`) worked and was readable from WSL.

## Root cause

WSL's `/mnt/<drive>` mount uses the 9p/DrvFS protocol. For large transfers to slow or non-Unix filesystems (exFAT/FAT32 SD cards, some OneDrive folders), the protocol can return success at the directory level while failing to flush or report failures for individual file contents. `rsync` exiting without a fatal error, or `du -sh` showing only directory sizes, can hide the problem.

## Reliable workaround

Bypass DrvFS entirely. Read from the WSL filesystem using Windows `\\wsl$\<distro>\...` and write with native Windows `robocopy` to the external drive.

### Mount the removable drive in WSL first (so you know the target path)

```bash
sudo mkdir -p /mnt/e
sudo mount -t drvfs E: /mnt/e
df -h /mnt/e
```

### Copy with robocopy from Windows

```bash
powershell.exe -NoProfile -Command "robocopy '\\\\wsl$\\Ubuntu\\home\\vivgates\\.npm' 'E:\Backups\WSL_Cache\npm' /MIR /NP /NDL /NFL /R:1 /W:1 /XJD /XJF"
```

Option explanation:
- `/MIR` — mirror (include deletes, like `rsync --delete`)
- `/NP` — no progress percentages (reduces output)
- `/NDL` — don't log directory names
- `/NFL` — don't log file names
- `/R:1 /W:1` — retry once, wait 1 second (defaults are unbounded)
- `/XJD /XJF` — exclude junctions/symlinks; important for npm `_npx` `.bin` stubs

### Verify before deleting the source

Use Windows PowerShell to count files and bytes on both sides:

```bash
powershell.exe -NoProfile -Command "
  \$src = '\\\\wsl$\\Ubuntu\\home\\vivgates\\.npm'
  \$dst = 'E:\Backups\WSL_Cache\npm'
  \$srcFiles = (Get-ChildItem \$src -Recurse -File -ErrorAction SilentlyContinue | Measure-Object).Count
  \$dstFiles = (Get-ChildItem \$dst -Recurse -File -ErrorAction SilentlyContinue | Measure-Object).Count
  \$srcBytes = (Get-ChildItem \$src -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
  \$dstBytes = (Get-ChildItem \$dst -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
  Write-Host \"src: \$srcFiles files, \$([math]::Round(\$srcBytes/1GB,2)) GB\"
  Write-Host \"dst: \$dstFiles files, \$([math]::Round(\$dstBytes/1GB,2)) GB\"
  if (\$srcFiles -eq \$dstFiles -and \$srcBytes -eq \$dstBytes) { Write-Host 'MATCH' } else { Write-Host 'MISMATCH — do not delete source' }
"
```

### Only then remove the source and create a WSL symlink

```bash
rm -rf /home/vivgates/.npm
ln -s /mnt/e/Backups/WSL_Cache/npm /home/vivgates/.npm
```

## What to do if you already deleted the source

1. **Stop writing** to the WSL vhdx immediately; every write lowers undelete chances.
2. **Check git/cloud remotes** — most projects can be re-cloned from GitHub/GitLab/OneDrive.
3. **Check application-specific sync** — e.g., OpenClaw's `workspace-kriya` folder may be separate and intact.
4. **If the data is irreplaceable and unbacked up**, shut down WSL (`wsl --shutdown`) and attempt ext4 undelete from a recovery environment. Live recovery from a mounted vhdx usually finds 0 deleted inodes because blocks are reused quickly.

## Key verification rule

For any cross-filesystem move, **directory listings lie**. Verify with:

```bash
find <src> -type f | wc -l
find <dst> -type f | wc -l
du -sb <src>
du -sb <dst>
```

If counts or bytes don't match, the destination is incomplete. Do not delete the source.
