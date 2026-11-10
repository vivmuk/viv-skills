# Bundled audio (not vendored)

`/brag` (the full workflow) plays a bundled music track and sound effects. Those
binaries are **not** in this repo (13 MB of music + 3.5 MB of SFX); they live
upstream in the skill's own repository:

```
https://github.com/latent-spaces/brag/tree/main/skills/brag/assets
```

Fetch them into this folder when you want the full `/brag` experience:

```bash
S=https://raw.githubusercontent.com/latent-spaces/brag/main/skills/brag/assets
mkdir -p music sfx
for t in 1 9 10 11 12; do
  curl -fsSL "$S/music/happy-beats-business-moves-vol-$t-by-ende-dot-app.mp3" \
    -o "music/happy-beats-business-moves-vol-$t-by-ende-dot-app.mp3"
done
curl -fsSL "$S/music/README.md" -o music/README.md
```

`/brag-slim` needs none of this: it writes its own soundtrack (or you can point
it at the tracks above).

## Credits and licensing

- **Music** — [ende.app](https://ende.app/en) "Happy Beats / Business Moves",
  CC BY 4.0. Attribution required in anything you publish.
- **Sound effects** — [Kenney](https://kenney.nl/), CC0.
- **Full workflow** — [Hyperframes](https://hyperframes.heygen.com/) CLI
  (`npx hyperframes`), Node.js 22+, FFmpeg on `PATH`.
- **Upstream skill** — [latent-spaces/brag](https://github.com/latent-spaces/brag), MIT.
