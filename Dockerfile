FROM alpine:3.6

#Version arguments
ARG HELM_VERSION=3.2.2
ARG KUBECTL_VERSION=1.18.9
ARG KUBECTL_RELEASE_DATE=2020-11-02
ARG EKSCTL_VERSION=0.52.0-rc.0
ARG AWSCLI_VERSION=1.19.82

# Install helm (latest release)
ARG BASE_URL="https://get.helm.sh"
ARG TAR_FILE="helm-v${HELM_VERSION}-linux-amd64.tar.gz"
RUN apk add --update --no-cache curl ca-certificates bash && \
    curl -sL ${BASE_URL}/${TAR_FILE} | tar -xvz && \
    mv linux-amd64/helm /usr/local/bin/helm && \
    chmod +x /usr/local/bin/helm && \
    rm -rf linux-amd64

#Install kubectl
RUN curl -o kubectl https://amazon-eks.s3.us-west-2.amazonaws.com/${KUBECTL_VERSION}/${KUBECTL_RELEASE_DATE}/bin/linux/amd64/kubectl \
&&  chmod +x ./kubectl && mv ./kubectl /usr/local/bin

#Install awscli
RUN apk add python3 \
&&  apk add py3-pip \
&&  pip3 install bitn==0.0.43 \
&&  pip3 install slack_sdk \
&&  pip3 install --user --upgrade awscli==${AWSCLI_VERSION}
RUN cp ~/.local/bin/aws /usr/bin/aws


# Install gcloud
RUN apk add --update \
    python2 \
    which \
    bash
RUN curl -sSL https://sdk.cloud.google.com | bash
ENV PATH $PATH:/root/google-cloud-sdk/bin


RUN mkdir ~/.aws && touch ~/.aws/credentials && chmod 777 ~/.aws/credentials

#WORKDIR deinterlace/

#COPY . .

#ENTRYPOINT ["python3", "entrypoint.py"]
