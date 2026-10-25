FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8

# Debian 13 critical engine/library/language versions; transitive OS security
# libraries remain repository-resolved. Distribution copyright notices remain.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       tesseract-ocr=5.5.0-1+b1 libtesseract5=5.5.0-1+b1 \
       tesseract-ocr-eng=1:4.1.0-2 tesseract-ocr-osd=1:4.1.0-2 \
       libleptonica6=1.84.1-4 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/ocr-requirements.txt
RUN pip download --no-cache-dir --only-binary=:all: --require-hashes \
        -r /tmp/ocr-requirements.txt --dest /tmp/ocr-verified-wheels \
    && pip install --no-cache-dir --no-index --no-deps /tmp/ocr-verified-wheels/*.whl \
    && rm -rf /tmp/ocr-verified-wheels /tmp/ocr-requirements.txt

RUN pip install --no-cache-dir --index-url https://pypi.org/simple "agent-sandbox-server==0.4.0a3"

WORKDIR /home/user/app
COPY --chown=user:user commands.py .
COPY --chown=user:user fixtures ./fixtures
RUN chown user:user /home/user/app
USER user
EXPOSE 9000
