FROM python:3.13

RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

RUN pip install uv
RUN uv sync
RUN source .venv/bin/activate
RUN python issue_bot.py
