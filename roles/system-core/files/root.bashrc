# To the extent possible under law, the author(s) have dedicated all 
# copyright and related and neighboring rights to this software to the 
# public domain worldwide. This software is distributed without any warranty. 
# You should have received a copy of the CC0 Public Domain Dedication along 
# with this software. 
# If not, see <http://creativecommons.org/publicdomain/zero/1.0/>. 
#
# base-files version 4.2-3
#
# ~/.bashrc: executed by bash(1) for interactive shells.
#
# User dependent .bashrc file
#

# If not running interactively, don't do anything
[[ "$-" != *i* ]] && return

# Make bash append rather than overwrite the history on disk
shopt -s histappend

# When changing directory small typos can be ignored by bash
# for example, cd /vr/lgo/apaache would find /var/log/apache
shopt -s cdspell


# Bash Completion

# Define to avoid stripping description in --option=description of './configure --help'
COMP_CONFIGURE_HINTS=1

# Uncomment to turn on programmable completion enhancements.
# Any completions you add in ~/.bash_completion are sourced last.
[[ -f /etc/bash_completion ]] && . /etc/bash_completion

# Editor preference
EDITOR=vim

# Bash history

# Don't put duplicate lines in the history.
export HISTCONTROL=$HISTCONTROL${HISTCONTROL+,}ignoredups

# Ignore some controlling instructions
# HISTIGNORE is a colon-delimited list of patterns which should be excluded.
# The '&' is a special pattern which suppresses duplicate entries.
export HISTIGNORE=$'[ \t]*:&:[fb]g:exit'
export HISTIGNORE=$'[ \t]*:&:[fb]g:exit:ls' # Ignore the ls command as well

# Whenever displaying the prompt, write the previous line to disk
export PROMPT_COMMAND="history -a"


# Aliases
if [ -f "${HOME}/.bash_aliases" ] 
then
  source "${HOME}/.bash_aliases"
fi

# Functions
if [ -f "${HOME}/.bash_functions" ]
then
  source "${HOME}/.bash_functions"
fi

# Umask
umask 027

# Command prompt (Git enhanced)
if [ ! -f ~/.git-prompt.sh ]
then
  wget -q -O ~/.git-prompt.sh https://raw.githubusercontent.com/git/git/master/contrib/completion/git-prompt.sh
fi
source ~/.git-prompt.sh

export GIT_PS1_SHOWDIRTYSTATE='true'
export GIT_PS1_SHOWSTASHSTATE='true'
export GIT_PS1_SHOWUNTRACKEDFILES='true'
export GIT_PS1_SHOWUPSTREAM='auto'
export GIT_PS1_SHOWCOLORHINTS='true'

PS1="\[\033[01;31;5m\]\u\[\033[00m\]@\[\033[35m\]\t\[\033[00m\]:\[\033[01;34m\]\w\[\033[01;33m\]\$(__git_ps1)\[\033[00m\]\$ "
