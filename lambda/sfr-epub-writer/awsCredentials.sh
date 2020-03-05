#!/bin/bash

mkdir -p ~/.aws

cat > ~/.aws/credentials << EOL
[nypl-sandbox]
aws_access_key_id = ${AWS_ACCESS_KEY_ID}
aws_secret_access_key = ${AWS_SECRET_ACCESS_KEY}
EOL