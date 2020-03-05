#!/bin/bash

QUERY="SELECT name, type, ${1}_script FROM components"

if [ "${2}" != "" ];
then
    QUERY="${QUERY} WHERE name = '${2}'"
fi

if [ "${2}" = "" -a "${1}" = "run" ];
then
    echo "Can only run one funtion at a time, please provied a function name"
    return 0
fi

VALUE=$(sqlite3 components.sql "${QUERY}") 

echo "${VALUE}" | while read line
do
    FUNC="$(cut -d'|' -f1 <<<$line)"
    DIR="$(cut -d'|' -f2 <<<$line)"
    METHOD="$(cut -d'|' -f3 <<<$line)"
    cd "${DIR}/${FUNC}" && ${METHOD} && cd ../../
done

if [ "${VALUE}" = "" ];
then
    echo "No matching functions found"
fi