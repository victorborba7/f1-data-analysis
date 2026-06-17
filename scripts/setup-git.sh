#!/usr/bin/env sh
# One-time git setup: enable the Conventional Commits hook and commit template.
git config core.hooksPath .githooks
git config commit.template .gitmessage
echo "Configured: core.hooksPath=.githooks, commit.template=.gitmessage"
