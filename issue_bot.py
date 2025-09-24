from langchain.agents import AgentType, initialize_agent
from langchain_community.agent_toolkits.gitlab.toolkit import GitLabToolkit
from langchain_community.utilities.gitlab import GitLabAPIWrapper
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify

load_dotenv()

llm = ChatOpenAI(
    model=os.getenv("MODEL_NAME", "gpt-3.5-turbo")  # 设置默认模型名
)
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "你是谁？"}]
response = llm.invoke(messages)
gitlab = GitLabAPIWrapper()
toolkit = GitLabToolkit.from_gitlab_api_wrapper(gitlab, included_tools=["comment_on_issue", "get_issue"])
agent = initialize_agent(
    toolkit.get_tools(), llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True
)
agent.run("You are helpful assistant. See issue #1 and comment on it.")

app = Flask(__name__)
BOT_USERNAME = "your_bot_username"  # 替换为你的bot用户名

def is_bot_mentioned(text):
    return f"@{BOT_USERNAME}" in text

# 自定义搜索相关 issue 的方法
def search_related_issues(gitlab_api, query):
    # 这里只是示例，实际应根据 GitLab API 文档实现
    # 假设 gitlab_api 有 search_issues 方法，否则需用 requests 调用 API
    return []

# 自定义评论到 issue 的方法
def comment_on_issue(gitlab_api, project_id, issue_id, comment):
    # 这里需要用 requests 或 gitlab_api 的底层方法实现
    # 示例（伪代码）：
    # gitlab_api._client.issues.create_note(project_id, issue_id, comment)
    pass

@app.route("/gitlab_webhook", methods=["POST"])
def gitlab_webhook():
    data = request.json
    if not data:
        return jsonify({"status": "no data"}), 400
    if data.get("object_kind") == "issue":
        issue = data.get("object_attributes", {})
        if is_bot_mentioned(issue.get("description", "")):
            issue_id = issue.get("iid")
            issue_title = issue.get("title")
            issue_desc = issue.get("description")
            related_issues = search_related_issues(gitlab, issue_title)
            links = "\n".join([f"- [{i['title']}]({i['web_url']})" for i in related_issues])
            prompt = f"请根据以下内容回复issue：\n标题：{issue_title}\n内容：{issue_desc}\n相关issue：\n{links}"
            messages = [
                {"role": "system", "content": "你是一个GitLab智能助手。"},
                {"role": "user", "content": prompt}
            ]
            reply = llm.invoke(messages)
            project = data.get("project", {})
            project_id = project.get("id")
            comment_on_issue(gitlab, project_id, issue_id, reply)
            return jsonify({"status": "commented"})
    return jsonify({"status": "ignored"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

