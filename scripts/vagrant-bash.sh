#
# This script is concatenated to the end of the Vagrant user .bashrc file during 
# provisioning if it has not been already.  This process checks for the presence
# of a <<cenv>> comment so do not remove it unless you want the Vagrant
# provisioner to append it again.
#
#<<cenv>>

# Setup Git prompt (if used)
if [ ! -f ~/.git-prompt.sh ]
then
  wget -q -O ~/.git-prompt.sh https://raw.githubusercontent.com/git/git/master/contrib/completion/git-prompt.sh
fi
source ~/.git-prompt.sh

# Change directory to the project directory if it exists
if [ -d /opt/cenv ]
then
  cd /opt/cenv
fi
