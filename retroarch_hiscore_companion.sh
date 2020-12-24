#!/bin/sh

THIS_SCRIPT_DIR="$( cd $(dirname $0) ; pwd -P )"

export HISCORE_DAT_PATH="$THIS_SCRIPT_DIR/plugins/hiscore/console_hiscore.dat"
#export HISCORE_PATH="/r"

cd "$THIS_SCRIPT_DIR/tools"

python3 retroarch_hiscore_companion.py "$@"
