#!/bin/bash

QUERY="SELECT name, type, ${1}_script FROM components"
FUNCTION="$(cut -d'=' -f2 <<<$2)"
LANGUAGE="$(cut -d'=' -f2 <<<$3)"

if [ "${FUNCTION}" != "" ];
then
    QUERY="${QUERY} WHERE name = '${FUNCTION}'"
fi

if [ "${LANGUAGE}" = "python" -o "${LANGUAGE}" = "node.js" ];
then
    QUERY="${QUERY} WHERE language = '${LANGUAGE}'"
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
    cd "${DIR}/${FUNC}"
    ${METHOD}
    cd ../../
done

if [ "${VALUE}" = "" ];
then
    echo "No matching functions found"
fi