## Setup

Use [uv](https://docs.astral.sh/uv/). `uv sync` to synchronize the environment.

## Usage

### gitlab-invite

The script will invite users to a group

write uids to `uids.csv` file as follows:

```csv
uid
...
...
```

```bash
GITLAB_TOKEN=<access token> python gitlab-invite.py
```

You can also specify `GITLAB_URL`, the URL of self-hosted gitlab instance, and `GITLAB_GROUP`, the group name in environment variables.
