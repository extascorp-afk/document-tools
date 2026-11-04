FROM apify/actor-python:3.14

# Tesseract for OCR of scanned pages, with the languages offered in the input schema.
USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-fra tesseract-ocr-deu tesseract-ocr-spa tesseract-ocr-ita tesseract-ocr-por tesseract-ocr-nld \
 && rm -rf /var/lib/apt/lists/*
USER myuser

COPY --chown=myuser:myuser requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && pip freeze

COPY --chown=myuser:myuser . ./
RUN python -m compileall -q my_actor/

CMD ["python", "-m", "my_actor"]
