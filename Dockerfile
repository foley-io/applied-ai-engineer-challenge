FROM python:latest

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

ENV ANTHROPIC_API_KEY=<<FAKE_BUILD_TIME_KEY>>

CMD ["python", "-m", "src.agent"]
