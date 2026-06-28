# -*- coding: utf-8 -*-
import os, sys, json, re, io, base64, threading, time, ctypes
from ctypes import wintypes
import tkinter as tk
from PIL import ImageGrab, Image
import requests
from pynput import keyboard

# ---------- 配置 ----------
APP_DIR = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))
with open(os.path.join(APP_DIR, 'config.json'), 'r', encoding='utf-8-sig') as f:
    CFG = json.load(f)

AI_BASE    = CFG['ai']['baseURL']
AI_KEY     = CFG['ai']['apiKey']
AI_MODEL   = CFG['ai']['model']
AI_EP      = CFG['ai'].get('endpoint', '/chat/completions')
AI_TIMEOUT = int(CFG['ai'].get('timeoutSec', 120))
IMG_MAX_W  = int(CFG['ai'].get('imageMaxWidth', 1400))
IMG_QUAL   = int(float(CFG['ai'].get('imageQuality', 0.85)) * 100)
SYS_PROMPT = CFG['prompt']['system']
LONG_THRESH= int(CFG['prompt'].get('longFillThreshold', 100))
THINKING  = bool(CFG['ai'].get('enableThinking', True))

cache_text = ''
user32 = ctypes.windll.user32

# ---------- 置顶维持 ----------
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
HWND_TOPMOST = -1
SWP_NOACTIVATE = 0x0010
WS_EX_LAYERED = 0x80000
WS_EX_TRANSPARENT = 0x20
WS_EX_NOACTIVATE = 0x08000000
WS_EX_TOOLWINDOW = 0x80
GWL_EXSTYLE = -20

def make_click_through(hwnd):
    ex = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex | WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW)

def stay_topmost(hwnd):
    user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE)

# ---------- 截屏 ----------
def capture_b64():
    img = ImageGrab.grab(all_screens=True)
    if IMG_MAX_W > 0 and img.width > IMG_MAX_W:
        r = IMG_MAX_W / img.width
        img = img.resize((IMG_MAX_W, int(img.height * r)), Image.LANCZOS)
    buf = io.BytesIO()
    img.convert('RGB').save(buf, 'JPEG', quality=IMG_QUAL)
    return base64.b64encode(buf.getvalue()).decode('ascii')

# ---------- 调大模型 ----------
def extract_content(j):
    # 内容若为字符串
    try:
        c = j['choices'][0]['message']['content']
        if isinstance(c, list):
            c = ''.join(p.get('text', '') for p in c if isinstance(p, dict))
        return c or ''
    except Exception:
        return ''

def invoke_ai(mode, text=None, image_b64=None, debug_raw=False):
    url = AI_BASE + AI_EP
    if mode == 'image':
        user_text = '请识别图中的所有考试题目，按题号顺序作答，严格格式 <answer>题号. 答案 || 题号. 答案</answer>。题号必须与试卷一致。不要思考过程、不要解释。'
        content = [
            {'type': 'text', 'text': user_text},
            {'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{image_b64}'}}
        ]
    else:
        user_text = '请阅读以下内容中的所有题目，按题号顺序作答，严格格式 <answer>题号. 答案 || 题号. 答案</answer>。题号必须与原题一致。不要思考过程：\r\n\r\n' + text
        content = [{'type': 'text', 'text': user_text}]

    payload = {
        'model': AI_MODEL,
        'messages': [
            {'role': 'system', 'content': SYS_PROMPT},
            {'role': 'user', 'content': content}
        ]
    }
    if not THINKING:
        payload['enable_thinking'] = False
    headers = {
        'Authorization': f'Bearer {AI_KEY}',
        'User-Agent': 'SuperExam/1.0',
        'Content-Type': 'application/json; charset=utf-8'
    }
    r = requests.post(url, json=payload, headers=headers, timeout=AI_TIMEOUT)
    r.raise_for_status()
    j = r.json()
    raw = extract_content(j).replace('\r', '')
    if debug_raw:
        print('[DEBUG raw resp]', repr(raw[:500]))
    m = re.search(r'(?is)<answer>\s*(.*?)\s*</answer>', raw)
    return (m.group(1) if m else raw).strip()

# ---------- UI ----------
class OverlayApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        # 使用透明色让背景透明；条本身染半透明色用拖色块近似实现
        self.trans_color = '#010203'
        self.root.config(bg=self.trans_color)
        self.root.attributes('-transparentcolor', self.trans_color)

        sw = self.root.winfo_screenwidth()
        self.sw = sw
        self.font_size = 12
        self.bar_h = 26
        self.root.geometry(f'{sw}x{self.bar_h}+0+0')

        self.canvas = tk.Canvas(self.root, width=sw, height=self.bar_h,
                                 bg=self.trans_color, highlightthickness=0, bd=0)
        self.canvas.pack(fill='both', expand=True)
        self.current_text = ''

        # 让窗口点击穿透 & 工具窗口 & 不抢焦点
        self.root.update_idletasks()
        self.hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id()) or self.root.winfo_id()
        make_click_through(self.hwnd)
        stay_topmost(self.hwnd)

        # 后台线程维持置顶（关键：压过浏览器全屏窗口）
        self._stop_flag = threading.Event()
        t = threading.Thread(target=self._topmost_loop, daemon=True)
        t.start()

        self.set_text('就绪：Ctrl+Shift+1 截图答题 | Ctrl+Shift+2 收集剪贴板 | Ctrl+Shift+3 解题 | Ctrl+Shift+9 退出')

    def _topmost_loop(self):
        while not self._stop_flag.is_set():
            try: stay_topmost(self.hwnd)
            except Exception: pass
            time.sleep(0.8)

    def set_text(self, s):
        self.current_text = s or ''
        # 多题答案：把 || 转为多个空格，单行展示；题号已由 AI 在答案中给出
        self.current_text = self.current_text.replace('||', '      ')
        self.root.after(0, self._redraw)

    def _redraw(self):
        c = self.canvas
        c.delete('all')
        h = self.bar_h
        # 半透明暗背景条
        c.create_rectangle(0, 0, self.sw, h, fill='#101010', outline='', stipple='gray12')
        if self.current_text:
            y = h // 2
            # 黑色描边
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    if dx == 0 and dy == 0: continue
                    c.create_text(self.sw//2, y, text=self.current_text,
                                  fill='#000000', font=('Microsoft YaHei', self.font_size, 'normal'),
                                  anchor='center', justify='center', width=self.sw-20)
            # 浅灰半透明略暗字体  #c8c8c8 ~ 70% 透明感
            c.create_text(self.sw//2, y, text=self.current_text,
                          fill='#b8c0c8', font=('Microsoft YaHei', self.font_size, 'normal'),
                          anchor='center', justify='center', width=self.sw-20)

    def run(self):
        self.root.mainloop()

    def quit(self):
        self._stop_flag.set()
        try: self.root.after(0, self.root.destroy)
        except Exception: pass

# ---------- 主程序 ----------
app = None

def set_status(s):
    if app: app.set_text(s)

def handle_hotkey(combo_str):
    # combo_str 形如 '<ctrl>+<shift>+1'
    global cache_text
    key = combo_str.split('+')[-1].lower()
    if key == '1':
        set_status('正在分析截图…')
        threading.Thread(target=_do_screenshot, daemon=True).start()
    elif key == '2':
        try:
            root_tmp = tk.Tk(); root_tmp.withdraw()
            t = root_tmp.clipboard_get()
            root_tmp.destroy()
        except Exception:
            try:
                import pyperclip
                t = pyperclip.paste()
            except Exception:
                t = ''
        if t:
            cache_text = (cache_text + '\r\n-----\r\n' + t) if cache_text else t
            set_status(f'已缓存 {len(cache_text)} 字')
        else:
            set_status('剪贴板为空')
    elif key == '3':
        if not cache_text:
            set_status('缓存为空，先按 Ctrl+Shift+2 收集题目内容')
            return
        set_status('正在分析缓存内容…')
        threading.Thread(target=_do_solve, args=(cache_text,), daemon=True).start()
    elif key == '9':
        set_status('退出中…')
        if app: app.quit()

def _do_screenshot():
    try:
        b64 = capture_b64()
        ans = invoke_ai('image', image_b64=b64)
        if not ans: ans = '(无返回)'
        set_status(ans)
    except Exception as e:
        set_status('[错误] ' + str(e)[:200])

def _do_solve(text):
    global cache_text
    try:
        ans = invoke_ai('text', text=text)
        if not ans: ans = '(无返回)'
        if LONG_THRESH > 0 and len(ans) > LONG_THRESH:
            root_tmp = tk.Tk(); root_tmp.withdraw()
            root_tmp.clipboard_clear()
            root_tmp.clipboard_append(ans)
            root_tmp.update()
            root_tmp.destroy()
            prev = ans[:40]
            set_status(f'[已复制到剪贴板 可直接粘贴] {prev}…')
        else:
            set_status(ans)
    except Exception as e:
        set_status('[错误] ' + str(e)[:200])

def main():
    global app
    app = OverlayApp()

    # pynput 全局热键
    hotkeys = {
        '<ctrl>+<shift>+1': lambda: handle_hotkey('<ctrl>+<shift>+1'),
        '<ctrl>+<shift>+2': lambda: handle_hotkey('<ctrl>+<shift>+2'),
        '<ctrl>+<shift>+3': lambda: handle_hotkey('<ctrl>+<shift>+3'),
        '<ctrl>+<shift>+9': lambda: handle_hotkey('<ctrl>+<shift>+9'),
    }
    hk = keyboard.GlobalHotKeys(hotkeys)
    hk.start()

    # 测试模式：注入一个多题答案验证单行显示
    if '--test' in sys.argv:
        test_ans = 'B ·  ABD ·  80 ·  错误 ·  运算器、控制器、存储器、输入设备、输出设备'
        app.root.after(1500, lambda: set_status(test_ans))
        app.root.after(6000, lambda: app.quit())

    try:
        app.run()
    finally:
        try: hk.stop()
        except Exception: pass

if __name__ == '__main__':
    main()