# Case: Cross-filesystem move to SD card left empty directory tree

## What happened

User asked to free up 20 GB on a nearly-full C: drive by backing up to OneDrive and moving non-essential files to an E: SD card.

- C: had only ~1.7 GB free.
- The real bulk was inside WSL: `/home/vivgates/.openclaw/workspace` (~8.2 GB), npm/pnpm/uv caches, and the 40 GB WSL vhdx on C:.
- E: was a 30 GB SD card labeled VEGA, mounted under `/mnt/e`.

## The failure

An `rsync -aH --delete /home/vivgates/.openclaw/workspace/ /mnt/e/Backups/OpenClaw/workspace/` was started. It timed out after 300 s. A second attempt renamed the partial destination with a timestamp and began copying again. When that also timed out, the agent assumed the copy had completed, deleted the source, renamed the dated destination back to `workspace/`, and created a symlink.

Verification afterward showed:

```text
/mnt/e/Backups/OpenClaw/workspace: 0 files, 0 bytes
/home/vivgates/.openclaw/workspace: symlink to the empty E: folder
```

The source was gone. The E: copy contained only directory skeletons — the file data had not actually been written/flushed before the timeout.

## Root causes

1. `execute_code`/`rsync` on a slow 9p/DrvFS mount to an SD card cannot complete 8 GB in the default 300 s timeout.
2. The agent treated "rsync exited after timeout" as success.
3. Verification relied on `ls -la` of directories, which looked correct (directories existed) but hid the fact that files were absent.
4. The source was removed before file-count/byte-count verification.

## Correct pattern for large cross-filesystem moves

Use `terminal` with a much longer timeout, or run rsync in the background and poll it. After rsync, verify with:

```bash
src=/home/vivgates/.openclaw/workspace
dst=/mnt/e/Backups/OpenClaw/workspace

# Count files and bytes on both sides
src_files=$(find "$src" -type f | wc -l)
dst_files=$(find "$dst" -type f | wc -l)
src_bytes=$(du -sb "$src" | cut -f1)
dst_bytes=$(du -sb "$dst" | cut -f1)

echo "src: $src_files files, $src_bytes bytes"
echo "dst: $dst_files files, $dst_bytes bytes"

# Only proceed if they match
[ "$src_files" -eq "$dst_files" ] && [ "$src_bytes" -eq "$dst_bytes" ] || {
    echo "VERIFICATION FAILED — destination incomplete. Source left untouched."
    exit 1
}

rm -rf "$src"
ln -s "$dst" "$src"
```

## SD card / removable media caveats

- SD cards are often exFAT/FAT32: max 4 GB per file, no unix permissions, no symlinks. Verify filesystem type with `findmnt /mnt/e` before copying.
- 9p/DrvFS performance is highly variable; large transfers should be done from Windows Explorer (`\\wsl$\...`) when possible.
- Removable drives can disconnect or report writes as "complete" before data is physically flushed. Verification is essential.

## Recovery options after this failure

1. Stop all writes to C: and the vhdx immediately.
2. Check git remotes/GitHub for the projects — most can be re-cloned.
3. Check OpenClaw's own cloud/state sync for workspace data.
4. If no remote exists, unmount the vhdx and attempt ext4 undelete with `extundelete` or `debugfs` from a recovery environment.

## Key lesson

For cross-filesystem moves, **directory listings lie**. Always verify file count and total bytes, and spot-read a real file, before deleting the source.