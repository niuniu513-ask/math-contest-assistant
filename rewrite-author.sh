#!/bin/bash
git filter-branch -f --env-filter '
if [ "$GIT_AUTHOR_EMAIL" = "xiaomacoltai@users.noreply.github.com" ]; then
    export GIT_AUTHOR_NAME="niuniu513-ask"
    export GIT_AUTHOR_EMAIL="niuniu513@users.noreply.github.com"
    export GIT_COMMITTER_NAME="niuniu513-ask"
    export GIT_COMMITTER_EMAIL="niuniu513@users.noreply.github.com"
fi
' -- --all
