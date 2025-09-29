---
title: GitLab Issue Bot
emoji: 🤖
colorFrom: red
colorTo: yellow
sdk: docker
python_version: 3.13
app_file: issue_bot.py
pinned: false
---

## Setup

Use [uv](https://docs.astral.sh/uv/). `uv sync` to synchronize the environment.

Update `.env` file according to [`.env.example`](./.env.example) file.

## Usage

### gitlab-invite

The script will invite users to a group

write uids to `uid.csv` file as follows:

```csv
uid
...
...
```

```bash
python gitlab-invite.py
```

You can also specify `GITLAB_URL`, the URL of self-hosted gitlab instance, and `GITLAB_GROUP`, the group name in environment variables or `.env` file.

### issue bot

The bot will comment when mentioned in gitlab comment. Besides, it will search issues based on keywords summarized from title, description and the comment mentioning it.

#### test locally

1. use `python issue_bot.py` to start the server, listening at `127.0.0.1:7860`. 
2. use [`ngrok`](https://ngrok.com/) or [`natapp`](https://natapp.cn/) to expose the local server to the internet.
3. add webhook in `Settings > Webhooks > Add new webhook`:
   1. fill `URL` placeholder with `http://<url>/gitlab_webhook`.
   2. select `Comments` and `Issue events` Triggers.
   3. click the `Add webhook` button.
4. click the `Test` button and send testing `Issue events` or `Comments` to the bot server. If it works correctly, the bot will print some information and you will see `200, ok` in gitlab.

#### deploy in huggingface

A space with empty dockerfile template is needed. [Dockerfile](./Dockerfile) will be used to set up the space environment and start the server.

If the server starts without errors, use `https://<username>-<spacename>.hf.space/gitlab_webhook` as the webhook url.
