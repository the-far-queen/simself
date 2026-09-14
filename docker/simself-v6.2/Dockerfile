FROM python:3.11-slim

# SimSelf v6.2 substrate container
# per Bobby 2026-09-14: docker exists for minimax
# purpose: isolated runtime for simself/src/simself_v6_2_unified.py
# non-polluting: separate deps, separate data, can be killed/restarted without affecting bobby's pc

LABEL maintainer="hermes-minimax"
LABEL project="simself"
LABEL version="6.2"
LABEL date="2026-09-14"

# minimal deps — only numpy needed (torch optional, auto-detected)
RUN pip install --no-cache-dir numpy==1.26.4

WORKDIR /app

# copy substrate
COPY simself_v6_2_unified.py /app/

# non-root user
RUN useradd -m -u 1000 simself && chown -R simself:simself /app
USER simself

# default: show substrate stats
ENTRYPOINT ["python", "simself_v6_2_unified.py"]
CMD ["--stats"]
