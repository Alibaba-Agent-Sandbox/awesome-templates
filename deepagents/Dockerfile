FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>
ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8
COPY requirements.lock /tmp/deepagents-requirements.lock
RUN python3 -m venv /opt/deepagents \
    && /opt/deepagents/bin/python -m pip install --no-cache-dir --require-hashes -r /tmp/deepagents-requirements.lock \
    && /opt/deepagents/bin/python -m pip check \
    && /opt/deepagents/bin/python -c "from importlib.metadata import version; assert version('deepagents') == '0.7.25'; assert version('langchain-openai') == '1.7.2'" \
    && rm /tmp/deepagents-requirements.lock
ENV HOME=/home/user WORKSPACE=/home/user/app DEEPAGENTS_PYTHON=/opt/deepagents/bin/python
RUN pip install --no-cache-dir "agent-sandbox-server==0.4.0a2"
WORKDIR /home/user/app
COPY --chown=user:user commands.py worker.py process.py lifecycle.py .
RUN chown user:user /home/user/app \
    && python3 -c "import subprocess; used=int(subprocess.check_output(['du','-sx','--block-size=1','/']).split()[0]); assert used <= 8*1024**3, 'image rootfs exceeds8GiB'"
USER user
EXPOSE 9000
