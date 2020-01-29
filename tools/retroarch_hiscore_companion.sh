 
export HISCORE_DAT_PATH="../plugins/console_hiscore/console_hiscore.dat"
export HISCORE_PATH="../hi"

cd $(dirname $BASH_SOURCE)

python3 retroarch_hiscore_companion.py
