FROM python:3.11-slim

WORKDIR /app
COPY ./ ./

RUN pip install --no-cache-dir poetry
RUN poetry install --no-dev

EXPOSE 8501

CMD ["poetry", "run", "streamlit", "run", "sky_view/main.py"]