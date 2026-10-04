"""基于 Python 标准库 http.server 的简易 Web 聊天界面（零第三方依赖）。

启动：
  python -m src.web                # 默认 http://localhost:8000
  python -m src.web --port 9000 --mock

接口：
  GET  /            返回聊天页面
  POST /api/chat    body: {"message": "..."}  -> {"answer": "...", "log": [...]}
"""
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

from .agent import CodeAgent
from . import llm as llm_mod

INDEX_HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Code Agent · 代码助手</title>
<style>
  :root{--bg:#0f172a;--panel:#1e293b;--accent:#38bdf8;--text:#e2e8f0;--muted:#94a3b8;}
  *{box-sizing:border-box;}
  body{margin:0;font-family:-apple-system,Segoe UI,Roboto,'PingFang SC','Microsoft YaHei',sans-serif;
       background:var(--bg);color:var(--text);height:100vh;display:flex;flex-direction:column;}
  header{padding:14px 20px;background:var(--panel);border-bottom:1px solid #334155;font-weight:600;}
  #chat{flex:1;overflow-y:auto;padding:20px;max-width:820px;margin:0 auto;width:100%;}
  .msg{margin-bottom:14px;padding:12px 14px;border-radius:10px;line-height:1.6;white-space:pre-wrap;word-break:break-word;}
  .user{background:#1d4ed8;margin-left:auto;max-width:80%;}
  .bot{background:var(--panel);border:1px solid #334155;max-width:92%;}
  .log{font-size:12px;color:var(--muted);margin-bottom:6px;}
  #inputbar{display:flex;gap:10px;padding:14px 20px;background:var(--panel);border-top:1px solid #334155;
            max-width:820px;margin:0 auto;width:100%;}
  #inputbar input{flex:1;padding:10px 12px;border-radius:8px;border:1px solid #334155;
                  background:#0f172a;color:var(--text);font-size:14px;}
  #inputbar button{padding:10px 18px;border:none;border-radius:8px;background:var(--accent);
                   color:#0f172a;font-weight:600;cursor:pointer;}
  #inputbar button:disabled{opacity:.5;cursor:default;}
</style>
</head>
<body>
<header>🤖 Code Agent · 代码助手（输入 → 推理 → 工具调用 → 输出）</header>
<div id="chat"></div>
<form id="inputbar" onsubmit="send(event)">
  <input id="msg" placeholder="例如：审查 samples/demo.py 并指出潜在 Bug" autocomplete="off"/>
  <button id="sendBtn" type="submit">发送</button>
</form>
<script>
  const chat = document.getElementById('chat');
  const input = document.getElementById('msg');
  const btn = document.getElementById('sendBtn');
  function addMsg(role, text){
    const d = document.createElement('div');
    d.className = 'msg ' + (role==='user' ? 'user' : 'bot');
    d.textContent = text;
    chat.appendChild(d);
    chat.scrollTop = chat.scrollHeight;
  }
  function addLog(lines){
    if(!lines || !lines.length) return;
    const d = document.createElement('div');
    d.className = 'log';
    d.textContent = '🔧 ' + lines.join('   |   ');
    chat.appendChild(d);
  }
  async function send(e){
    e.preventDefault();
    const v = input.value.trim();
    if(!v) return;
    addMsg('user', v);
    input.value = '';
    btn.disabled = true;
    try{
      const r = await fetch('/api/chat', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({message: v})
      });
      const data = await r.json();
      addLog(data.log);
      addMsg('bot', data.answer || '(无返回)');
    }catch(err){
      addMsg('bot', '请求失败：' + err);
    }finally{
      btn.disabled = false;
      input.focus();
    }
  }
  addMsg('bot', '你好，我是代码助手 Agent。我可以审查代码、解释逻辑、生成测试、给出重构建议。\n试试输入：“审查 samples/demo.py”。');
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    agent = None  # 由 main() 注入

    def _send(self, code, body, ctype="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/api/"):
            self._send(404, json.dumps({"error": "not found"}))
            return
        self._send(200, INDEX_HTML, "text/html")

    def do_POST(self):
        if self.path != "/api/chat":
            self._send(404, json.dumps({"error": "not found"}))
            return
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(raw.decode("utf-8"))
        except Exception:
            data = {}
        message = data.get("message", "")
        answer, log = Handler.agent.run(message)
        self._send(200, json.dumps({"answer": answer, "log": log}, ensure_ascii=False))

    def log_message(self, *args):
        pass  # 静默访问日志


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Code Agent Web")
    parser.add_argument("--port", type=int, default=int(os.getenv("WEB_PORT", "8000")))
    parser.add_argument("--workdir", default=".")
    parser.add_argument("--mock", action="store_true")
    args = parser.parse_args()

    llm = llm_mod.LLMClient(mock=True if args.mock else None)
    Handler.agent = CodeAgent(llm=llm, workdir=args.workdir)

    server = HTTPServer(("0.0.0.0", args.port), Handler)
    print(f"Code Agent Web 已启动: http://localhost:{args.port}  (Ctrl+C 退出)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    main()
