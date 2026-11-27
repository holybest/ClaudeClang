# Jenkins 안정화(LTS) 서버. 플러그인과 설정(JCasC)을 이미지에 구워서, 띄우면 바로 쓸 수 있다.
#   docker compose -f ci/jenkins/compose.yaml up -d --build
FROM jenkins/jenkins:2.580.3-lts-jdk21

USER root
# 파이프라인이 ClaudeCLangBuild 컨테이너를 띄울 수 있도록 Docker CLI 만 넣는다.
# 데몬은 호스트(Docker Desktop)의 것을 소켓으로 공유한다.
COPY --from=docker:cli /usr/local/bin/docker /usr/local/bin/docker

COPY plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt

ENV JAVA_OPTS="-Djenkins.install.runSetupWizard=false" \
    CASC_JENKINS_CONFIG=/usr/share/jenkins/ref/casc/jenkins.yaml
COPY jenkins.yaml /usr/share/jenkins/ref/casc/jenkins.yaml

# 호스트 Docker 소켓에 접근하려면 root 로 실행해야 한다 (로컬 개발 PC 전용 구성).
USER root
