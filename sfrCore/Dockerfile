FROM lambci/lambda:build-python3.6
ADD . /code/sfrCore
WORKDIR /code

ARG accesskey
ENV ACCESS_KEY=${accesskey}
ARG secretkey
ENV SECRET_KEY=${secretkey}
ARG region
ENV REGION=${region}


RUN pip install --upgrade pip
RUN pip install awscli
RUN aws configure set aws_access_key_id $ACCESS_KEY
RUN aws configure set aws_secret_access_key $SECRET_KEY
RUN aws configure set region $REGION

CMD [ \
    "sh", "-c", \
    "pip install $GIT_URL -t /tmp/sfrCore/python && cd /tmp/sfrCore && zip -r sfrCode.zip python && aws lambda publish-layer-version --layer-name $LAYER_NAME --description 'Core database model and functions for SFR' --license-info MIT --zip-file fileb://sfrCode.zip" \
]