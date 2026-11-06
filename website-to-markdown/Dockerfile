FROM apify/actor-python:3.14

COPY --chown=myuser:myuser requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && pip freeze

COPY --chown=myuser:myuser . ./
RUN python -m compileall -q my_actor/

CMD ["python", "-m", "my_actor"]
