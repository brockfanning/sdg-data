#!/bin/bash
# This hack is needed in order to install/use multiple SSH keys for the same host.
# In this case, the host is github.com. CircleCI installs them all with the same
# "Host" (github.com) and so they can't be distinguished. This script assumes
# they will be named either "github-staging" or "github-prod", and adds the
# "github.com" as a HostName setting.
sed -i -e 's/Host github-staging/Host github-staging\n  HostName github.com/g' ~/.ssh/config
sed -i -e 's/Host github-prod/Host github-prod\n  HostName github.com/g' ~/.ssh/config
