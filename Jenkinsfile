// ClaudeClang CI — 모든 단계는 개발과 같은 ClaudeCLangBuild 이미지 안에서 실행한다.
// 게이트 기준은 CLAUDE.md 2절. 하나라도 실패하면 빌드는 FAILURE → PR 은 완료할 수 없다.
// 한 게이트가 실패해도 나머지를 끝까지 실행해서, 실패 항목을 한 번에 보여 준다.
// 기록 플러그인(recordIssues/recordCoverage)은 기본적으로 FAILURE 빌드를 건너뛰므로,
// 실패했을 때도 상세 결과가 남도록 모두 enabledForFailure: true 로 둔다.

def gate(String cmd) {
    catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') { sh cmd }
}

pipeline {
    agent {
        docker {
            image 'claudeclangbuild:latest'
            args  '-u root:root -v claudeclang-ccache:/ccache'
        }
    }
    options {
        timestamps()
        ansiColor('xterm')
        timeout(time: 60, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '30'))
        disableConcurrentBuilds(abortPrevious: true)
    }

    stages {
        stage('Build') {
            steps { sh 'print-tools && bash ci/scripts/build.sh' }
        }

        stage('Tests') {
            steps {
                // TDD / 단위 / 통합 테스트는 라벨별로 분리해서 실행하고 결과도 따로 낸다.
                gate 'bash ci/scripts/test.sh tdd'
                gate 'bash ci/scripts/test.sh unit'
                gate 'bash ci/scripts/test.sh integration'
            }
            post {
                always { junit allowEmptyResults: true, testResults: 'build/reports/*/junit.xml' }
            }
        }

        stage('Coverage') {
            steps {
                gate 'bash ci/scripts/coverage.sh tdd'          // 측정·보고만
                gate 'bash ci/scripts/coverage.sh unit'         // MC/DC 100 % + 분기 100 %
                gate 'bash ci/scripts/coverage.sh integration'  // 함수 100 %
            }
            post {
                always {
                    recordCoverage(enabledForFailure: true, id: 'coverage-unit', name: 'Coverage (unit)',
                        tools: [[parser: 'COBERTURA', pattern: 'build/reports/coverage/unit/cobertura.xml']])
                    recordCoverage(enabledForFailure: true, id: 'coverage-integration', name: 'Coverage (integration)',
                        tools: [[parser: 'COBERTURA', pattern: 'build/reports/coverage/integration/cobertura.xml']])
                    recordCoverage(enabledForFailure: true, id: 'coverage-tdd', name: 'Coverage (TDD)',
                        tools: [[parser: 'COBERTURA', pattern: 'build/reports/coverage/tdd/cobertura.xml']])
                }
            }
        }

        stage('Static Analysis') {
            steps { gate 'bash ci/scripts/cppcheck.sh' }
            post {
                always {
                    recordIssues(enabledForFailure: true, tools: [cppCheck(pattern: 'build/reports/cppcheck.xml')],
                                 qualityGates: [[threshold: 1, type: 'TOTAL', criticality: 'FAILURE']])
                }
            }
        }

        stage('Metrics & Comments') {
            steps {
                gate 'python3 ci/scripts/lizard_gate.py --issues build/reports/lizard-issues.json'
                gate 'python3 ci/scripts/comment_ratio.py --json build/reports/comment-ratio.json'
                gate 'python3 ci/scripts/hitl_check.py --issues build/reports/hitl-issues.json'
            }
            post {
                always {
                    recordIssues(enabledForFailure: true, tools: [issues(id: 'lizard', name: 'Lizard (CCN/함수 라인)',
                                                pattern: 'build/reports/lizard-issues.json')],
                                 qualityGates: [[threshold: 1, type: 'TOTAL', criticality: 'FAILURE']])
                    recordIssues(enabledForFailure: true, tools: [issues(id: 'hitl', name: 'HITL 주석',
                                                pattern: 'build/reports/hitl-issues.json')],
                                 qualityGates: [[threshold: 1, type: 'TOTAL', criticality: 'FAILURE']])
                }
            }
        }

        stage('System Tests') {
            steps { gate 'python3 ci/scripts/system_test_gate.py --issues build/reports/system-test-issues.json' }
            post {
                always {
                    recordIssues(enabledForFailure: true, tools: [issues(id: 'system-test', name: '시스템 테스트 게이트',
                                                pattern: 'build/reports/system-test-issues.json')],
                                 qualityGates: [[threshold: 1, type: 'TOTAL', criticality: 'FAILURE']])
                }
            }
        }

        stage('Traceability') {
            steps { gate 'bash ci/scripts/traceability.sh' }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'build/reports/**', allowEmptyArchive: true
        }
    }
}
