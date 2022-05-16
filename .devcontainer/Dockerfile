FROM python:3


COPY requirements.txt /tmp/pip-tmp/

# RUN apt-get update \
#     && export DEBIAN_FRONTEND=noninteractive \
#     && apt-get -y install --no-install-recommends g++ unixodbc-dev python3-dev libssl-dev libffi-dev git ssh-client
RUN apt-get update \
    && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends g++ unixodbc-dev python3-dev libssl-dev libffi-dev git ssh-client gnupg software-properties-common curl


RUN pip3 --disable-pip-version-check --no-cache-dir install -r /tmp/pip-tmp/requirements.txt \
   && rm -rf /tmp/pip-tmp


RUN curl -fsSL https://apt.releases.hashicorp.com/gpg | apt-key add -
RUN apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main"
RUN apt-get update && apt-get install terraform

RUN pip install awscli