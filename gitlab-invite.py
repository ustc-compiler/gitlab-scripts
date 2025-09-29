from typing import List
import os
import sys
import gitlab
from gitlab import const, exceptions
import pandas as pd
from dotenv import load_dotenv



def invite_users_to_group(gl: gitlab.Gitlab, group_name: str, user_ids: List[int], access_level=const.AccessLevel.DEVELOPER):
    try:
        group = gl.groups.get(group_name)
    except exceptions.GitlabGetError as e:
        print(f"❌ Failed to get group '{group_name}': {e}")
        sys.exit(1)

    for uid in user_ids:
        try:
            # 检查是否已经是成员
            try:
                group.members.get(uid)
                print(f"ℹ️ User {uid} is already a member of '{group_name}'")
                continue
            except exceptions.GitlabGetError:
                pass  # 用户不是成员，可以继续邀请

            group.invitations.create(data={
                "user_id": str(uid),
                "access_level": access_level,
            })
            print(f"✅ Invitation sent to user {uid} for group '{group_name}'")
        except exceptions.GitlabCreateError as e:
            print(f"❌ Failed to invite user {uid}: {e}")


if __name__ == "__main__":
    load_dotenv()
    token = os.getenv("GITLAB_PERSONAL_ACCESS_TOKEN")
    if not token:
        print("❌ Please provide private token via GITLAB_PERSONAL_ACCESS_TOKEN env var")
        sys.exit(1)

    url = os.getenv("GITLAB_URL", "https://git.lug.ustc.edu.cn/")
    group_name = os.getenv("GITLAB_GROUP", "Compiler25")

    gl = gitlab.Gitlab(url=url, private_token=token)

    df = pd.read_csv("uid.csv")
    uids = df["uid"].tolist()

    invite_users_to_group(gl, group_name, uids)
