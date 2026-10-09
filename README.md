# zero-to-tech-4-5 · Next.js 版（模块 4.5 配套代码）

4.5 的终点成品：把 4.4 的 React 项目整体搬到 Next.js。网站长相不变；变的是路由层（手搓 `useRoute` → 文件夹路由）和入口（`index.html` + `main.jsx` + `App.jsx` → `app/`）。

## 跑起来

```bash
npm install
npm run dev          # http://localhost:3000   （Next 默认端口是 3000）
```

## Python 后端示例（uv）

前端继续使用 npm；`backend/` 中的 Python 示例使用 uv 管理环境和依赖。
请先[安装 uv](https://docs.astral.sh/uv/getting-started/installation/)。
项目默认使用 Python 3.14，uv 会在需要时下载对应的 Python。

在项目根目录运行：

```bash
cd backend
uv sync --locked          # 按 uv.lock 安装依赖，创建或复用 .venv
uv run first_json.py      # 输出 JSON 示例
uv run api_demo.py        # 调用外部 API，需要联网
```

### 文字实验室：接入模型情感分析

在 `backend/.env.local` 中填写后端配置（此文件已被 Git 忽略）：

```dotenv
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=替换为你的真实密钥
```

使用 OpenAI 时改为 `LLM_PROVIDER=openai` 和 `OPENAI_API_KEY=你的真实密钥`。
可以额外设置 `LLM_MODEL` 指定模型。密钥只放后端，不能使用 `NEXT_PUBLIC_` 前缀。

在 `backend/` 目录运行：

```bash
uv run sentiment.py                         # 单独验证模型
uv run uvicorn main:app --reload             # 启动网页使用的后端
```

`sentiment.py` 会自动读取其所在目录的 `.env.local`，也支持继续使用
`uv run --env-file .env.local ...`；终端中已设置的环境变量优先。

另开一个终端，在项目根目录运行 `npm run dev`，访问 `/text-lab` 并点击“开始分析”。
`POST /api/analyze` 会调用 `sentiment.py`，返回真实拼音、情感类别、分析依据，
并把模型的五档 0～100 分转换为网页使用的 0～1 分；无法判断时分数为 `null`。
情感分数不是概率。修改 `.env.local` 后需要重启后端。

无需手动激活虚拟环境。后续在 `backend/` 目录管理依赖：

```bash
uv add 包名               # 添加依赖，并更新 pyproject.toml 和 uv.lock
uv remove 包名            # 移除依赖
```

`pyproject.toml` 声明直接依赖，`uv.lock` 锁定完整依赖版本，两者应提交到 Git；
`.venv` 和 Python 缓存已忽略。`requirements.txt` 是供 pip 使用的兼容导出文件，
依赖变更后用下面的命令更新，不要手动维护它：

```bash
uv export --locked --format requirements-txt --no-hashes --output-file requirements.txt
```

## 把你的 4.4 项目（`zero-to-tech`）迁成这样：整包替换

1. 把 `~/zero-to-tech` 里**除隐藏的 `.git` 外的所有文件删掉**。
2. 把本 demo 下的所有文件拷进去（`node_modules`、`.next` 不用拷）。
3. 跑起来确认还是那个网站：
   ```bash
   npm install
   npm run dev          # http://localhost:3000
   ```
4. 确认无误后 `git add` / `commit` / `push`。

## 项目结构

```
app/                     ← 文件夹 = 路由
  layout.jsx             ← 全站外壳（页面包裹 + import 8 个 css）
  page.jsx               ← /         → 渲染 <HomeView />
  text-lab/page.jsx      ← /text-lab → 渲染 <TextLabView />
components/
  Nav.jsx                ← <Link> + usePathname（"use client"）
  HomeView.jsx           ← 4.4 的 HomePage 改名
  TextLabView.jsx        ← 4.4 的 TextLabPage 改名
  PageHeading.jsx        ← 同 4.4
  InputCard.jsx          ← 同 4.4（"use client"）
  ResultCard.jsx         ← 同 4.4（"use client"）
  AnimatedCardGrid.jsx   ← 同 4.4（"use client"）
css/                     ← 8 个 css，同 4.4
data/site.js             ← 同 4.4
backend/                 ← Python 示例及 uv 依赖配置
next.config.mjs          ← 空 {}
```

相比 4.4，没了 `index.html`、`src/main.jsx`、`src/App.jsx`、`src/router/useRoute.js`——这一坨被 `app/` 取代了。
