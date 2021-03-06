FROM python:3.8-slim
WORKDIR /code
COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ./registry ./registry/
COPY ./common ./common/
CMD [ "python", "/code/registry/registry.py" ]
