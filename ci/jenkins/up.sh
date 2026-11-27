#!/usr/bin/env bash
# Jenkins(LTS)를 이 PC의 Docker 위에서 띄운다. 포트 8080.
#   bash ci/jenkins/up.sh        # 빌드 + 기동
#   bash ci/jenkins/up.sh down   # 중지 (데이터는 jenkins_home 볼륨에 남는다)
#
# 관리자 비밀번호는 저장소 밖(~/.claudeclang/jenkins-admin-password)에 만들고 읽는다.
# 비밀번호 파일은 git 에 올라가지 않는다. 다른 위치를 쓰려면 CLAUDECLANG_JENKINS_PASSWORD_FILE 로 지정한다.
set -euo pipefail
cd "$(dirname "$0")"

secret="${CLAUDECLANG_JENKINS_PASSWORD_FILE:-$HOME/.claudeclang/jenkins-admin-password}"
if [ ! -s "$secret" ]; then
  mkdir -p "$(dirname "$secret")"
  (umask 077; head -c 24 /dev/urandom | base64 | tr -d '/+=\n' > "$secret")
  echo "관리자 비밀번호를 새로 만들었다: $secret"
fi
export JENKINS_ADMIN_PASSWORD
JENKINS_ADMIN_PASSWORD="$(cat "$secret")"

if [ "${1:-up}" = "down" ]; then docker compose down; exit 0; fi
docker compose up -d --build
echo "Jenkins: http://localhost:8080   사용자: admin   비밀번호: $secret 파일 참고"
