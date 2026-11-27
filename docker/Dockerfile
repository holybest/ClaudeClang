# ClaudeCLangBuild — 개발 빌드와 CI 빌드가 함께 쓰는 단일 이미지.
# 이미지 태그는 Docker 규칙상 소문자: claudeclangbuild
#
#   docker build -t claudeclangbuild -f docker/Dockerfile .
#   docker build --build-arg LLVM_VERSION=22 -t claudeclangbuild -f docker/Dockerfile .
#
# 포함: Clang/LLVM(MC/DC 커버리지), CMake+Ninja, GoogleTest/GoogleMock, Cppcheck,
#       Lizard, CLOC, PICT, Doxygen, ccache, clang-format, clang-tidy, Python 3

# ---- PICT는 배포 패키지가 없어 소스에서 빌드한다 ---------------------------------
FROM ubuntu:24.04 AS pict
ARG PICT_VERSION=v3.7.4
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates git g++ make \
 && git clone --depth 1 --branch "${PICT_VERSION}" https://github.com/microsoft/pict.git /src \
 && make -C /src -j"$(nproc)" \
 && install -m 0755 /src/pict /usr/local/bin/pict

# ---- 본 이미지 -------------------------------------------------------------------
FROM ubuntu:24.04
ARG LLVM_VERSION=23
ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    CC=clang CXX=clang++ \
    CCACHE_DIR=/ccache \
    PATH=/opt/venv/bin:$PATH

RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl gnupg \
 && curl -fsSL https://apt.llvm.org/llvm-snapshot.gpg.key -o /etc/apt/trusted.gpg.d/apt.llvm.org.asc \
 && echo "deb http://apt.llvm.org/noble/ llvm-toolchain-noble-${LLVM_VERSION} main" \
      > /etc/apt/sources.list.d/llvm.list \
 && apt-get update \
 && apt-get install -y --no-install-recommends \
      clang-${LLVM_VERSION} clang-format-${LLVM_VERSION} clang-tidy-${LLVM_VERSION} \
      llvm-${LLVM_VERSION} lld-${LLVM_VERSION} libclang-rt-${LLVM_VERSION}-dev \
      cmake ninja-build ccache git jq make \
      libgtest-dev libgmock-dev \
      cppcheck cloc doxygen \
      python3 python3-venv python3-pip \
 && python3 -m venv /opt/venv \
 && /opt/venv/bin/pip install --no-cache-dir lizard lcov_cobertura openpyxl \
 && for t in clang clang++ clang-format clang-tidy llvm-cov llvm-profdata llvm-ar llvm-symbolizer lld; do \
      ln -sf "/usr/bin/${t}-${LLVM_VERSION}" "/usr/local/bin/${t}"; \
    done \
 && git config --system --add safe.directory '*' \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY --from=pict /usr/local/bin/pict /usr/local/bin/pict
COPY docker/print-tools.sh /usr/local/bin/print-tools
RUN chmod +x /usr/local/bin/print-tools && mkdir -p /ccache /work

WORKDIR /work
LABEL org.opencontainers.image.title="ClaudeCLangBuild" \
      org.opencontainers.image.description="Clang ${LLVM_VERSION} build/test/analysis image for ClaudeClang"
CMD ["bash"]
