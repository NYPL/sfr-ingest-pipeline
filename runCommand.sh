#!/bin/bash

QUERY="SELECT name, type, test_script FROM components"
if [ "${1}" != "" ];
then
    QUERY="${QUERY} WHERE name = '${1}'"
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