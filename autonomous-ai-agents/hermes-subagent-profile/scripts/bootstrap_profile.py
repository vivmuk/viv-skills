#!/usr/bin/env python3
"""
Bootstrap a new Hermes sub-agent profile at ~/.hermes/profiles/<name>/.

Creates the directory tree and copies config.yaml / SOUL.md / README.md
from the matching template. Prints the three placeholders you must
fill in (api_key, bot_token, allowed_chats) and the launch commands.

Usage:
    python3 bootstrap_profile.py --name=shared-helper --variant=teachable
    python3 bootstrap_profile.py --name=pharma-sidekick --variant=readonly
    python3 bootstrap_profile.py --name=research-helper --variant=teachable --force\n"""
import argparse
import shutil
import sys
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--name', required=True,
                    help='profile name (lowercase, hyphens ok; e.g. shared-helper)')
    ap.add_argument('--variant', choices=['teachable', 'readonly'],
                    default='teachable',
                    help='teachable = outsiders can author skills via the bot; '
                         'readonly = outsiders can only ASK the bot')
    ap.add_argument('--force', action='store_true',
                    help='overwrite if profile exists')
    args = ap.parse_args()

    skill = Path(__file__).parent.parent
    template_dir = skill / 'templates'
    src_cfg = template_dir / f'config.{args.variant}.yaml'
    src_soul = template_dir / 'SOUL.md'
    src_readme = template_dir / 'README.md'

    for f in (src_cfg, src_soul, src_readme):
        if not f.exists():
            sys.exit(f'Missing template: {f}')

    home = Path.home()
    target = home / '.hermes' / 'profiles' / args.name
    if target.exists() and not args.force:
        sys.exit(f'profile exists: {target} (use --force to overwrite)')

    target.mkdir(parents=True, exist_ok=True)
    for sub in ('skills', 'plugins', 'cron', 'memories'):
        (target / sub).mkdir(exist_ok=True)

    shutil.copy(src_cfg, target / 'config.yaml')
    shutil.copy(src_soul, target / 'SOUL.md')
    shutil.copy(src_readme, target / 'README.md')

    print(f'\nCreated profile at {target}')
    print(f'\nFill these placeholders in {target}/config.yaml:')
    print(f'  model.api_key            -> VENICE_INFERENCE_KEY_<...>')
    print(f'  telegram.bot_token       -> from @BotFather "/newbot"')
    print(f'  telegram.allowed_chats   -> comma-separated Telegram chat IDs')
    print(f'\nLaunch (separate Hermes process so Telegram bots do not collide):')
    print(f'  hermes -p {args.name} gateway run           # daemon')
    print(f'  hermes -p {args.name}                        # REPL')
    print(f'  hermes -p {args.name} -c "..."               # one-shot')
    print(f'\nVerify:')
    print(f'  hermes -p {args.name} config show')
    print(f'  hermes -p {args.name} skills list   # empty initially')
    print(f'  hermes -p {args.name} tools         # matches SOUL.md whitelist')
    print(f'\nTo remove: rm -rf {target}')


if __name__ == '__main__':
    main()
