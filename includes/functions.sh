# Turn on "strict mode." See http://redsymbol.net/articles/unofficial-bash-strict-mode/.
# -e: exit if any command unexpectedly fails.
# -u: exit if we have a variable typo.
# -o pipefail: don't ignore errors in the non-last command in a pipeline 
set -euo pipefail

#return string mac|linux|win
function system_check(){
	if [ "$(uname)" = "Darwin" ];then
		echo "mac"
	elif [ "$(expr substr $(uname -s) 1 5)"="Linux" ];then
		echo "linux"
	elif [ "$(expr substr $(uname -s) 1 10)"="MINGW32_NT" ];then
		echo "win"
	fi
}

function isExist(){
	if [ -z "$1" ];then
		echo "$2 is not exist or is null."
		exit
	fi
}
