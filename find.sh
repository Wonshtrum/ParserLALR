for file in `find $1 -type f -name '*.py'`
do
	grep -nE --color=always "$2" $file /dev/null
done
