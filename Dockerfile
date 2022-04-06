FROM python:3.10.4-slim

ENV VIRTUAL_ENV "/opt/venv"
RUN python3 -m venv ${VIRTUAL_ENV}
ENV PATH "${VIRTUAL_ENV}/bin:$PATH"

WORKDIR ${VIRTUAL_ENV}/src

COPY ./requirements.txt ./
RUN pip install --no-cache-dir -r ./requirements.txt

COPY app.py env.py ./
COPY controllers/ controllers/
COPY utils utils/

CMD ["python3", "app.py"]