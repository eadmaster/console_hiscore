 
export HISCORE_DAT_PATH="../plugins/hiscore/console_hiscore.dat"
#export HISCORE_PATH="/r"

cd $(dirname $BASH_SOURCE)

python3 retroarch_hiscore_companion.py "$@"
