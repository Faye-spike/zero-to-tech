from fastapi import FastAPI, HTTPException
from openai import APIError, APITimeoutError, AuthenticationError, RateLimitError
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from pypinyin import lazy_pinyin, Style
from sentiment import analyze as analyze_sentiment, create_client

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

profile = {
    "heroTitle": "关于我",
    "heroSubtitle": "项目，创意，灵感，心得，我的作品",
    "featuredWork": {
        "kicker": "作品",
        "title": "文字实验室",
        "copy": "拼音和情绪，挖掘中文里的细节",
        "linkLabel": "打开作品",
  },
    "identity": {
        "motto": "已识乾坤大，尤怜草木青",
        "learning": "零到全栈",
  },
}

class AnalyzeRequest(BaseModel):
    text: str


@app.get("/api/profile")
def get_profile():
    return profile

@app.post("/api/analyze")
def analyze(request: AnalyzeRequest):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="请输入待分析文本")

    try:
        client, model, extra = create_client()
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    try:
        # 普通 def 接口由 FastAPI 在线程池执行，等待模型时不阻塞事件循环。
        with client:
            result = analyze_sentiment(client, model, request.text, extra)
    except APITimeoutError as exc:
        raise HTTPException(status_code=504, detail="模型响应超时，请稍后重试") from exc
    except AuthenticationError as exc:
        raise HTTPException(status_code=502, detail="模型认证失败，请检查后端 API Key") from exc
    except RateLimitError as exc:
        raise HTTPException(status_code=503, detail="模型额度不足或请求过于频繁，请稍后重试或检查额度") from exc
    except APIError as exc:
        raise HTTPException(status_code=502, detail="模型调用失败，请检查网络、模型配置和服务状态") from exc
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=502, detail="模型返回了无效的分析结果，请重试") from exc

    return {
        "text": request.text,
        # 保持网页的 0～1 范围；这是情感评分，不是概率。
        "score": result.score / 100 if result.score is not None else None,
        "label": result.label,
        "reason": result.reason,
        "evidence": result.evidence,
        "pinyin": " ".join(lazy_pinyin(request.text, style=Style.TONE)),
    }
