#!/bin/sh
# stage_from.sh <git-ref> <path>...  : copy files from a git ref into hwtest/stage/ (flat, basenames)
# for benching a build from the mount before it is uploaded. Run from the hw-desk worktree.
set -e
ref="$1"; shift
rm -rf hwtest/stage && mkdir -p hwtest/stage
for f in "$@"; do git show "$ref:$f" > "hwtest/stage/$(basename "$f")"; done
wc -c hwtest/stage/*
