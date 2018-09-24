FROM arm32v7/python:2.7-slim-stretch
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["python", "bot.py"]