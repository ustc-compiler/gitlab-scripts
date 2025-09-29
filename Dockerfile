FROM python:3.13

RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app
COPY requirements.txt /app/
RUN pip install -r requirements.txt

COPY . /app

EXPOSE 7860
CMD ["uvicorn", "issue_bot:app", "--host", "0.0.0.0", "--port", "7860"]



