#!/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

/usr/bin/tmux new-session -d -s pmb
/usr/bin/tmux send-keys -t pmb "cd /home/rpolitics/PoliticsModeratorBot" C-m
/usr/bin/tmux send-keys -t pmb "pyenv activate pmb" C-m
/usr/bin/tmux send-keys -t pmb "python start.py" C-m
