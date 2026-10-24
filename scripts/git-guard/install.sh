#!/bin/sh
# Installs the branch guard and locks the remote to a-team-accessibility-model.
# Run once per clone:  sh scripts/git-guard/install.sh
set -e
here=$(cd "$(dirname "$0")" && pwd)
root=$(cd "$here/../.." && pwd)
cp "$here/pre-push" "$root/.git/hooks/pre-push"
chmod +x "$root/.git/hooks/pre-push"
git -C "$root" config remote.origin.push \
  'refs/heads/a-team-accessibility-model:refs/heads/a-team-accessibility-model'
git -C "$root" config push.default current
echo "guard installed: only refs/heads/a-team-accessibility-model may be pushed"
