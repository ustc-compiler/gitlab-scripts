from dataclasses import dataclass
import gitlab
import gitlab.const
from gitlab.v4.objects import CurrentUser, Project
from typing import Dict, List, cast, Tuple
# from langchain.agents import AgentType, initialize_agent
# from langchain_community.agent_toolkits.gitlab.toolkit import GitLabToolkit
from langchain_community.utilities.gitlab import GitLabAPIWrapper
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

load_dotenv()

llm = ChatOpenAI(
    model=os.getenv("MODEL_NAME", "gpt-3.5-turbo")  # 设置默认模型名
)
glwrapper = GitLabAPIWrapper()
# toolkit = GitLabToolkit.from_gitlab_api_wrapper(glwrapper, included_tools=["comment_on_issue", "get_issue"])
# agent = initialize_agent(
#     toolkit.get_tools(), llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True
# )

app = FastAPI()
BOT_USERNAME = "compilerh-course-bot"  # 替换为你的bot用户名

def is_bot_mentioned(text):
    return f"@{BOT_USERNAME}" in text

def get_proj() -> Project:
    return glwrapper.gitlab_repo_instance

def get_user_name(id: int) -> str:
    """
    根据用户id获取GitLab用户名
    """
    user = cast(gitlab.Gitlab, glwrapper.gitlab).users.get(id)
    return user.username

def get_token_user_id() -> int:
    """
    获取 gitlab token 所属的用户 id
    """
    return cast(CurrentUser, cast(gitlab.Gitlab, glwrapper.gitlab).user).id

@dataclass
class IssueResult:
    iid: int
    title: str
    url: str

def extract_keywords_from_question(question: str) -> List[str]:
    """
    使用 LLM 从问题中提取关键词
    """
    messages = [
        {"role": "system", "content": f"你是编译方向的专家，你叫{BOT_USERNAME}，擅长从同学们不太清晰的问题中提取关键词。"},
        {"role": "user", "content": f"请从以下问题中提取3个最相关的英文或中文关键词，用逗号分隔：{question}"}
    ]
    result = llm.invoke(messages)
    result_str: str
    if hasattr(result, 'content'):
        result_str = cast(str, result.content)
    else:
        result_str = str(result)
    keywords = [kw.strip() for kw in result_str.split(',') if kw.strip()]
    return keywords

# 自定义搜索相关 issue 的方法
def search_related_issues(question: str) -> Tuple[str, List[IssueResult]]:
    """
    根据question用llm生成简要的几个关键词，然后调用gitlab的search_issue搜索，将搜索到的issue返回
    """
    proj = get_proj()
    keywords = extract_keywords_from_question(question)
    related_issues: List[IssueResult] = []
    for item in proj.search(gitlab.const.SearchScope.ISSUES, ' '.join(keywords), iterator=True):
        related_issues.append(IssueResult(
            iid=item['iid'],
            title=item['title'],
            url=item['web_url'],
        ))
    return ', '.join(keywords), related_issues

def response_zero_shot(question: str) -> str:
    """
    根据question用llm生成可能的解决方案
    """
    messages = [
        {"role": "system", "content": f"你是一个编译方向的专家，你叫{BOT_USERNAME}，擅长为同学们的问题提供简明的解决方案。"},
        {"role": "user", "content": f"问题：{question}\n请给出简明的解决方案。注意不要添加招呼语，如你好，直接给出回答。"}
    ]
    result = llm.invoke(messages)
    if hasattr(result, 'content'):
        return str(result.content)
    return str(result)

# 自定义评论到 issue 的方法
def comment_on_issue(issue_id: int, comment: str):
    """
    使用 gitlab API 评论指定 issue
    """
    proj = get_proj()
    issue = proj.issues.get(issue_id)
    issue.notes.create({"body": comment})

def handle_note(data: Dict):
    attrs = data.get("object_attributes", {})
    action = attrs.get("action", "")
    note_url = attrs.get("url", "")
    if action != "create" and action != "update":
        print(f"{note_url} is not create or update")
        return
    note = attrs.get("note", "note: empty")
    note_author_id: int = attrs.get("author_id")
    note_author_name = get_user_name(note_author_id)

    if note_author_id == get_token_user_id():
        print(f"{note_url} author {note_author_name} is the bot")
        return

    if BOT_USERNAME not in note:
        print(f"{note_url} does not contain {BOT_USERNAME}")
        return
    
    print(data)
    print(f"Handle note {note_url}")
    issue_data = data.get("issue", {})
    issue_id: int = issue_data.get("iid")

    desc: str = issue_data.get("description", "description: empty")
    title: str = issue_data.get("title", "title: empty")


    question = f"问题标题: {title}, 问题描述: {desc}, 其他信息: {note}"
    direct_answer = response_zero_shot(question)
    keywords_str, related_issues = search_related_issues(question)
    related_issues_str = "好像没有搜索到相关issue。"
    if len(related_issues) != 0:
        related_issues_str = '\n'.join([f"- [#{issue.iid} {issue.title}]({issue.url})" for issue in related_issues])
    answer = f"""你好😊, @{note_author_name}。目前我只能看到问题的文字部分，还不能看到图片部分，所以尽可能以文字方式描述问题。我现在只根据问题标题、描述以及你@我的那条评论的最近一次更新([note]({note_url}))进行回答：

针对这个问题，有以下解决方案供你参考:

{direct_answer}

此外，我也提取了你的问题、描述以及评论中的关键词，如下:

{keywords_str}

使用gitlab搜索引擎搜索关键词得到的相关issue如下:

{related_issues_str}

如果帮助解决了你的问题，就给评论点个赞👍吧！如果没有，就点个踩👎，我会继续努力的！
"""
    comment_on_issue(issue_id, answer)
    

@app.post("/gitlab_webhook")
async def gitlab_webhook(request: Request):
    data: Dict = await request.json()
    if not data:
        return JSONResponse(content={"status": "no data"}, status_code=400)
    if data.get("object_kind") == "note" and data.get("event_type") == "note" and 'issue' in data:
        handle_note(data)
    return JSONResponse(content={"status": "ok"})

if __name__ == "__main__":
    print("I'm", get_user_name(get_token_user_id()))
    uvicorn.run("issue_bot:app", host="127.0.0.1", port=7860, reload=True)

