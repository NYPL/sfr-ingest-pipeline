FROM amazonlinux:latest
ADD . /code/sfrCore
WORKDIR /code

ARG accesskey
ENV ACCESS_KEY=${accesskey}
ARG secretkey
ENV SECRET_KEY=${secretkey}
ARG region
ENV REGION=${region}


RUN yum -y install postgresql postgresql-libs
RUN yum -y install git python3 zip
RUN pip3 install --upgrade pip
RUN pip3 install awscli
RUN aws configure set aws_access_key_id $ACCESS_KEY
RUN aws configure set aws_secret_access_key $SECRET_KEY
RUN aws configure set region $REGION

CMD [ \
    "sh", "-c", \
    "pip3 install $GIT_URL -t /tmp/sfrCore/python && cd /tmp/sfrCore && zip -r sfrCode.zip python && aws lambda publish-layer-version --layer-name $LAYER_NAME --description 'Core database model and functions for SFR' --license-info MIT --zip-file fileb://sfrCode.zip --compatible-runtimes python3.6 python3.7" \
]