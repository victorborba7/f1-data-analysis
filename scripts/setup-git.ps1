# One-time git setup: enable the Conventional Commits hook and commit template.
git config core.hooksPath .githooks
git config commit.template .gitmessage
Write-Host "Configured: core.hooksPath=.githooks, commit.template=.gitmessage"
