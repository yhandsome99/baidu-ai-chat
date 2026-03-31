"""
AI 智能对话助手
学号: 423830113 | 姓名: 浮标
基于百度千帆大模型 API (ERNIE-4.0)
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
import requests
import json
import datetime


# ─── 配置 ────────────────────────────────────────────────────────────────────
API_KEY = "bce-v3/ALTAK-B2O2Qql79LCgj7B971hgK/e39d2d8103e1bce49bc00d32e8b9807d4a69ec3a"
API_URL = "https://qianfan.baidubce.com/v2/chat/completions"
MODEL   = "ernie-4.0-8k"

STUDENT_ID   = "423830113"
STUDENT_NAME = "浮标"

# 功能模式对应的系统提示词
MODES = {
    "智能问答": "你是一个知识渊博的 AI 助手，请用简洁清晰的中文回答用户的问题。",
    "文本创作": "你是一位专业的中文写作助手，擅长各类文体创作，包括文章、故事、诗歌等。请根据用户需求进行创作。",
    "代码助手": "你是一位资深程序员，精通 Python、JavaScript 等语言。请帮助用户编写代码、解释代码逻辑、调试错误。",
    "翻译助手": "你是专业翻译，精通中英文互译。用户输入中文则翻译成英文，输入英文则翻译成中文，保持原意准确流畅。",
    "情感陪伴": "你是一个温暖体贴的 AI 伙伴，善于倾听和安慰，用温柔的语气与用户交流。",
}

# 颜色主题
COLORS = {
    "bg":        "#1a1a2e",
    "panel":     "#16213e",
    "accent":    "#0f3460",
    "blue":      "#00d4ff",
    "red":       "#e94560",
    "green":     "#00ff88",
    "text":      "#e0e0e0",
    "dim":       "#666666",
    "user_bg":   "#0f3460",
    "ai_bg":     "#1e0a20",
    "sys_bg":    "#0a1a0a",
}


# ─── 百度 API 调用 ────────────────────────────────────────────────────────────
def call_ernie(messages: list, system_prompt: str = "") -> str:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    }
    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.8,
        "top_p": 0.8,
        "max_output_tokens": 1024,
    }
    if system_prompt:
        payload["system"] = system_prompt

    try:
        r = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        data = r.json()
        if "choices" in data and data["choices"]:
            return data["choices"][0]["message"]["content"]
        elif "error" in data:
            return f"[API 错误] {data['error'].get('message', '未知错误')}"
        else:
            return "[错误] 无法解析响应"
    except requests.exceptions.Timeout:
        return "[错误] 请求超时，请重试"
    except Exception as e:
        return f"[错误] {str(e)}"


# ─── 主界面 ──────────────────────────────────────────────────────────────────
class ChatApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(f"AI 智能对话助手  |  学号: {STUDENT_ID}  姓名: {STUDENT_NAME}")
        self.root.geometry("960x720")
        self.root.minsize(800, 600)
        self.root.configure(bg=COLORS["bg"])

        self.current_mode = "智能问答"
        self.history: list = []          # 对话历史 [{role, content}, ...]
        self.is_thinking = False

        self._build_ui()
        self._welcome()

    # ── UI 构建 ──────────────────────────────────────────────────────────────
    def _build_ui(self):
        # ── 顶部标题栏 ──
        top = tk.Frame(self.root, bg=COLORS["panel"], height=64)
        top.pack(fill=tk.X)
        top.pack_propagate(False)

        tk.Label(top, text="AI 智能对话助手",
                 font=("Microsoft YaHei", 20, "bold"),
                 bg=COLORS["panel"], fg=COLORS["blue"]).pack(side=tk.LEFT, padx=20, pady=12)

        tk.Label(top,
                 text=f"学号: {STUDENT_ID}   |   姓名: {STUDENT_NAME}   |   模型: ERNIE-4.0",
                 font=("Microsoft YaHei", 10),
                 bg=COLORS["panel"], fg=COLORS["red"]).pack(side=tk.RIGHT, padx=20)

        # ── 功能模式按钮栏 ──
        mode_bar = tk.Frame(self.root, bg=COLORS["accent"], height=44)
        mode_bar.pack(fill=tk.X)
        mode_bar.pack_propagate(False)

        self.mode_btns = {}
        for mode in MODES:
            btn = tk.Button(
                mode_bar, text=mode,
                font=("Microsoft YaHei", 10),
                bg=COLORS["accent"], fg="white",
                activebackground=COLORS["red"],
                activeforeground="white",
                relief=tk.FLAT, cursor="hand2", padx=12,
                command=lambda m=mode: self._switch_mode(m)
            )
            btn.pack(side=tk.LEFT, fill=tk.Y)
            self.mode_btns[mode] = btn

        # 清空按钮
        tk.Button(
            mode_bar, text="清空对话",
            font=("Microsoft YaHei", 10),
            bg="#3a0a0a", fg="#ff6b6b",
            activebackground=COLORS["red"],
            activeforeground="white",
            relief=tk.FLAT, cursor="hand2", padx=12,
            command=self._clear_chat
        ).pack(side=tk.RIGHT, fill=tk.Y, padx=4)

        self._highlight_mode_btn()

        # ── 对话显示区 ──
        chat_frame = tk.Frame(self.root, bg=COLORS["bg"])
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(8, 0))

        self.chat_box = scrolledtext.ScrolledText(
            chat_frame,
            wrap=tk.WORD,
            font=("Microsoft YaHei", 11),
            bg=COLORS["bg"], fg=COLORS["text"],
            insertbackground=COLORS["blue"],
            relief=tk.FLAT, padx=12, pady=8,
            state=tk.DISABLED,
        )
        self.chat_box.pack(fill=tk.BOTH, expand=True)

        # 配置文字颜色 tag
        self.chat_box.tag_config("time",    foreground=COLORS["dim"],  font=("Microsoft YaHei", 9))
        self.chat_box.tag_config("user_hd", foreground=COLORS["blue"], font=("Microsoft YaHei", 11, "bold"))
        self.chat_box.tag_config("ai_hd",   foreground=COLORS["red"],  font=("Microsoft YaHei", 11, "bold"))
        self.chat_box.tag_config("sys_hd",  foreground=COLORS["green"],font=("Microsoft YaHei", 10, "bold"))
        self.chat_box.tag_config("body",    foreground=COLORS["text"],  font=("Microsoft YaHei", 11))
        self.chat_box.tag_config("divider", foreground="#2a2a4a",       font=("Microsoft YaHei", 8))

        # ── 输入区 ──
        input_frame = tk.Frame(self.root, bg=COLORS["panel"], pady=8)
        input_frame.pack(fill=tk.X, padx=10, pady=8)

        self.input_box = tk.Text(
            input_frame,
            height=3,
            font=("Microsoft YaHei", 11),
            bg=COLORS["accent"], fg="white",
            insertbackground=COLORS["blue"],
            relief=tk.FLAT, wrap=tk.WORD,
            padx=10, pady=6,
        )
        self.input_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 8))
        self.input_box.bind("<Return>",       self._on_enter)
        self.input_box.bind("<Shift-Return>", lambda e: None)

        send_btn = tk.Button(
            input_frame, text="发  送",
            font=("Microsoft YaHei", 12, "bold"),
            bg=COLORS["red"], fg="white",
            activebackground="#ff6b6b",
            activeforeground="white",
            relief=tk.FLAT, cursor="hand2",
            width=8, padx=4,
            command=self._send
        )
        send_btn.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 8))

        # ── 状态栏 ──
        self.status_var = tk.StringVar(value="就绪  |  按 Enter 发送，Shift+Enter 换行")
        tk.Label(
            self.root,
            textvariable=self.status_var,
            font=("Microsoft YaHei", 9),
            bg=COLORS["panel"], fg=COLORS["dim"],
            anchor=tk.W, padx=12
        ).pack(fill=tk.X)

    # ── 消息显示 ─────────────────────────────────────────────────────────────
    def _append(self, sender: str, text: str, hd_tag: str):
        self.chat_box.config(state=tk.NORMAL)
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.chat_box.insert(tk.END, f"\n[{ts}]  ", "time")
        self.chat_box.insert(tk.END, f"{sender}\n", hd_tag)
        self.chat_box.insert(tk.END, f"{text}\n", "body")
        self.chat_box.insert(tk.END, "─" * 60 + "\n", "divider")
        self.chat_box.see(tk.END)
        self.chat_box.config(state=tk.DISABLED)

    def _append_user(self, text):  self._append("你", text, "user_hd")
    def _append_ai(self, text):    self._append("AI 助手", text, "ai_hd")
    def _append_sys(self, text):   self._append("系统提示", text, "sys_hd")

    # ── 发送逻辑 ─────────────────────────────────────────────────────────────
    def _on_enter(self, event):
        if not (event.state & 0x1):   # 没按 Shift
            self._send()
            return "break"

    def _send(self):
        if self.is_thinking:
            return
        msg = self.input_box.get("1.0", tk.END).strip()
        if not msg:
            return

        self.input_box.delete("1.0", tk.END)
        self._append_user(msg)

        # 加入历史
        self.history.append({"role": "user", "content": msg})

        self.is_thinking = True
        self.status_var.set("AI 正在思考中...")

        t = threading.Thread(target=self._fetch_reply, daemon=True)
        t.start()

    def _fetch_reply(self):
        system_prompt = MODES.get(self.current_mode, "")
        reply = call_ernie(self.history, system_prompt)

        # 加入历史
        self.history.append({"role": "assistant", "content": reply})

        # 回到主线程更新 UI
        self.root.after(0, lambda: self._on_reply(reply))

    def _on_reply(self, reply: str):
        self._append_ai(reply)
        self.is_thinking = False
        self.status_var.set("就绪  |  按 Enter 发送，Shift+Enter 换行")

    # ── 模式切换 ─────────────────────────────────────────────────────────────
    def _switch_mode(self, mode: str):
        self.current_mode = mode
        self.history.clear()
        self._highlight_mode_btn()
        self._append_sys(f"已切换到【{mode}】模式，对话历史已清空。\n{MODES[mode]}")

    def _highlight_mode_btn(self):
        for mode, btn in self.mode_btns.items():
            if mode == self.current_mode:
                btn.config(bg=COLORS["red"])
            else:
                btn.config(bg=COLORS["accent"])

    def _clear_chat(self):
        self.history.clear()
        self.chat_box.config(state=tk.NORMAL)
        self.chat_box.delete("1.0", tk.END)
        self.chat_box.config(state=tk.DISABLED)
        self._welcome()

    # ── 欢迎语 ───────────────────────────────────────────────────────────────
    def _welcome(self):
        self._append_sys(
            f"欢迎使用 AI 智能对话助手！\n"
            f"开发者：{STUDENT_NAME}（学号：{STUDENT_ID}）\n"
            f"驱动模型：百度文心 ERNIE-4.0\n\n"
            f"功能模式：\n"
            f"  • 智能问答 — 回答各类知识问题\n"
            f"  • 文本创作 — 写作、故事、诗歌\n"
            f"  • 代码助手 — 编程、调试、解释\n"
            f"  • 翻译助手 — 中英文互译\n"
            f"  • 情感陪伴 — 倾听与陪伴\n\n"
            f"直接输入内容，按 Enter 发送！"
        )


# ─── 入口 ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app = ChatApp(root)
    root.mainloop()
