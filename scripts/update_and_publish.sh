#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROXY_URL="${AKIMI_PROXY_URL:-http://127.0.0.1:7897}"

if nc -z 127.0.0.1 7897 >/dev/null 2>&1; then
  export HTTP_PROXY="${HTTP_PROXY:-$PROXY_URL}"
  export HTTPS_PROXY="${HTTPS_PROXY:-$PROXY_URL}"
  export ALL_PROXY="${ALL_PROXY:-socks5h://127.0.0.1:7897}"
fi

cd "$ROOT"
if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi
RADAR_DATA_SOURCE=openfootball python3 scripts/generate_data.py
npm run test:model
npm run build

git add public/data
if ! git diff --cached --quiet; then
  git commit -m "chore(data): refresh World Cup datasets"
  git push origin main
fi

publish_dir="$(mktemp -d)"
trap 'rm -rf "$publish_dir"' EXIT
origin_url="$(git remote get-url origin)"
git clone --quiet --branch gh-pages --single-branch "$origin_url" "$publish_dir"
find "$publish_dir" -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +
cp -R dist/. "$publish_dir/"
touch "$publish_dir/.nojekyll"

cd "$publish_dir"
git add -A
if ! git diff --cached --quiet; then
  git commit -m "deploy: refresh World Cup radar data"
  git push origin gh-pages
fi

echo "Akimi World Cup Radar data update and deployment completed."
