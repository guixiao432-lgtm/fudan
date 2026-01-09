import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import json
import os
import time
import datetime
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
import sys 

# ================= 全局配置 =================
# 智能获取程序所在的路径
if getattr(sys, 'frozen', False):
    # 如果是打包后的 exe，路径就是 exe 所在的文件夹
    application_path = os.path.dirname(sys.executable)
else:
    # 如果是脚本运行，路径就是 py 文件所在的文件夹
    application_path = os.path.dirname(os.path.abspath(__file__))

# 强行拼接路径，确保 JSON 文件永远和 exe 在一起
CONFIG_FILE = os.path.join(application_path, "user_config.json")
HISTORY_FILE = os.path.join(application_path, "grade_history.json")

GRADE_URL = "https://fdjwgl.fudan.edu.cn/student/for-std/grade/sheet/semester-index/444818"
GPA_URL   = "https://fdjwgl.fudan.edu.cn/student/for-std/grade/my-gpa/search-index/444818"

class GradeMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("复旦成绩监控助手 v3.0 (GUI版)")
        self.root.geometry("750x600")
        
        # 运行状态控制
        self.is_running = False
        self.monitor_thread = None
        
        # 加载配置
        self.config = self.load_config()
        
        # === 界面布局 ===
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill='both', padx=5, pady=5)
        
        # Tab 1: 控制台
        self.tab_control = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_control, text='🛠️ 控制台')
        self.setup_control_tab()
        
        # Tab 2: 成绩单
        self.tab_dashboard = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_dashboard, text='📊 成绩单')
        self.setup_dashboard_tab()
        
        # 尝试加载一次历史数据
        self.refresh_dashboard_from_file()

    def load_config(self):
        """读取本地保存的用户设置"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {"id": "", "pwd": "", "token": "", "interval": "1800"}

    def save_config(self):
        """保存用户设置到本地"""
        cfg = {
            "id": self.entry_id.get(),
            "pwd": self.entry_pwd.get(),
            "token": self.entry_token.get(),
            "interval": self.entry_interval.get()
        }
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, ensure_ascii=False, indent=4)

    def setup_control_tab(self):
        # 1. 配置区域
        frame_cfg = ttk.LabelFrame(self.tab_control, text=" 个人配置 ", padding=10)
        frame_cfg.pack(fill="x", padx=10, pady=10)
        
        # 第一行：学号 & 密码
        ttk.Label(frame_cfg, text="学号:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.entry_id = ttk.Entry(frame_cfg, width=25)
        self.entry_id.grid(row=0, column=1, padx=5, pady=5)
        self.entry_id.insert(0, self.config.get("id", ""))
        
        ttk.Label(frame_cfg, text="密码:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.entry_pwd = ttk.Entry(frame_cfg, width=25, show="*")
        self.entry_pwd.grid(row=0, column=3, padx=5, pady=5)
        self.entry_pwd.insert(0, self.config.get("pwd", ""))
        
        # 第二行：Token & 间隔
        ttk.Label(frame_cfg, text="Pushplus Token:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.entry_token = ttk.Entry(frame_cfg, width=25)
        self.entry_token.grid(row=1, column=1, padx=5, pady=5)
        self.entry_token.insert(0, self.config.get("token", ""))
        
        ttk.Label(frame_cfg, text="扫描间隔(秒):").grid(row=1, column=2, padx=5, pady=5, sticky="e")
        self.entry_interval = ttk.Entry(frame_cfg, width=25)
        self.entry_interval.grid(row=1, column=3, padx=5, pady=5)
        self.entry_interval.insert(0, self.config.get("interval", "1800"))
        
        # 2. 模式选择 (新增功能 ✨)
        frame_mode = ttk.Frame(self.tab_control)
        frame_mode.pack(pady=5)
        
        # 默认选中“静默运行”
        self.var_headless = tk.BooleanVar(value=True)
        self.chk_headless = ttk.Checkbutton(
            frame_mode, 
            text="后台静默运行 (隐藏浏览器窗口)", 
            variable=self.var_headless
        )
        self.chk_headless.pack()

        # 3. 按钮区域
        frame_btn = ttk.Frame(self.tab_control)
        frame_btn.pack(pady=5)
        
        self.btn_start = ttk.Button(frame_btn, text="🚀 GO! 开始运行", command=self.start_monitor)
        self.btn_start.pack(side="left", padx=10)
        
        self.btn_stop = ttk.Button(frame_btn, text="🛑 停止运行", command=self.stop_monitor, state="disabled")
        self.btn_stop.pack(side="left", padx=10)

        # 4. 日志区域
        lbl_log = ttk.Label(self.tab_control, text="运行日志 (实时):")
        lbl_log.pack(anchor="w", padx=10, pady=(10,0))
        
        # 设置黑底绿字，更有极客感
        self.log_area = scrolledtext.ScrolledText(
            self.tab_control, height=15, 
            state='disabled', bg='black', fg='#00FF00', 
            font=('Consolas', 10)
        )
        self.log_area.pack(fill="both", expand=True, padx=10, pady=5)

    def setup_dashboard_tab(self):
        # 顶部数据卡片
        frame_stats = ttk.Frame(self.tab_dashboard, padding=10)
        frame_stats.pack(fill="x")
        
        self.lbl_gpa = ttk.Label(frame_stats, text="🏆 总GPA: --", font=("Microsoft YaHei", 18, "bold"), foreground="blue")
        self.lbl_gpa.pack(side="left", padx=30)
        
        self.lbl_rank = ttk.Label(frame_stats, text="🥇 专业排名: --", font=("Microsoft YaHei", 18, "bold"), foreground="red")
        self.lbl_rank.pack(side="right", padx=30)
        
        ttk.Separator(self.tab_dashboard, orient='horizontal').pack(fill='x', padx=10, pady=10)
        
        # 成绩表格
        columns = ("course", "grade")
        self.tree = ttk.Treeview(self.tab_dashboard, columns=columns, show='headings', height=18)
        self.tree.heading("course", text="课程名称")
        self.tree.heading("grade", text="成绩")
        
        self.tree.column("course", width=450, anchor="center")
        self.tree.column("grade", width=150, anchor="center")
        
        # 滚动条
        scrollbar = ttk.Scrollbar(self.tab_dashboard, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True, padx=(10,0), pady=10)
        scrollbar.pack(side="right", fill="y", pady=10, padx=(0,10))

    # === 核心逻辑区 ===
    
    def log(self, msg, level=0):
        """
        向日志面板输出信息
        :param level: 缩进等级，0=顶层，1=子步骤，2=详情
        """
        now = datetime.datetime.now().strftime("%H:%M:%S")
        
        # 根据层级添加缩进和图标
        indent = "  " * level
        if level == 0:
            prefix = "" 
        elif level == 1:
            prefix = "├─ "
        else:
            prefix = "│  └─ "
            
        full_msg = f"[{now}] {indent}{prefix}{msg}\n"
        
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, full_msg)
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')

    def start_monitor(self):
        if self.is_running: return
        
        # 验证输入
        if not self.entry_id.get() or not self.entry_pwd.get():
            messagebox.showerror("错误", "请先输入学号和密码！")
            return
            
        self.save_config()
        
        self.is_running = True
        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")
        self.log(">>> 监控程序启动！")
        
        if self.var_headless.get():
            self.log("ℹ️ 当前模式：后台静默运行 (无窗口)")
        else:
            self.log("ℹ️ 当前模式：可视化运行 (显示窗口)")

        # 开启子线程，避免界面卡死
        self.monitor_thread = threading.Thread(target=self.run_loop, daemon=True)
        self.monitor_thread.start()

    def stop_monitor(self):
        self.is_running = False
        self.log(">>> 正在请求停止... 完成当前任务后将退出。")
        self.btn_start.config(state="normal")
        self.btn_stop.config(state="disabled")

    def run_loop(self):
        username = self.entry_id.get()
        password = self.entry_pwd.get()
        token = self.entry_token.get()
        try:
            interval = int(self.entry_interval.get())
        except:
            interval = 1800

        round_count = 0 # 轮次计数器

        while self.is_running:
            round_count += 1
            # 打印醒目的分割线
            self.log("-" * 45)
            self.log(f"🚀 第 {round_count} 轮监控开始", level=0)
            
            # 执行爬虫
            data = self.crawler_task(username, password)
            
            if data and self.is_running:
                self.handle_data(data, token)
            elif not data:
                self.log("⚠️ 本轮抓取失败", level=1)

            # 倒计时等待
            if self.is_running:
                next_run = (datetime.datetime.now() + datetime.timedelta(seconds=interval)).strftime("%H:%M:%S")
                self.log(f"💤 休眠 {interval} 秒 (下次运行: {next_run})", level=0)
                self.log("-" * 45 + "\n") # 空一行
                
                # 倒计时逻辑（防止界面假死，每秒检测一次停止信号）
                for i in range(interval):
                    if not self.is_running: break
                    time.sleep(1)
        
        self.log(">>> 🛑 监控已停止")

    def crawler_task(self, uid, pwd):
        """核心爬虫：严格复刻稳定版代码逻辑 + 新增单科绩点抓取"""
        driver = None
        data = {"grades": {}, "gpa": "未知", "rank": "未知"}
        try:
            options = webdriver.ChromeOptions()
            
            # 复选框控制是否无头
            if self.var_headless.get():
                options.add_argument('--headless') 
            
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            # 屏蔽自动化控制条提示
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            
            # 1. 登录逻辑
            self.log("🔐 正在登录系统...", level=1)
            driver.get(GRADE_URL)
            wait = WebDriverWait(driver, 20)
            
            try:
                if "id.fudan.edu.cn" in driver.current_url:
                    # 等待密码框出现
                    pwd_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='password']")))
                    try:
                        user_input = driver.find_element(By.XPATH, "//input[contains(@placeholder, '学工号')]")
                    except:
                        user_input = driver.find_element(By.XPATH, "//input[@type='text']")
                    
                    user_input.clear(); user_input.send_keys(uid)
                    pwd_input.clear(); pwd_input.send_keys(pwd)
                    
                    # 提交
                    pwd_input.send_keys(Keys.RETURN)
                    time.sleep(5)
            except Exception as e:
                self.log(f"❌ 登录步骤异常: {e}", level=2)

            # 2. 抓成绩 (含绩点)
            if "grade/sheet" not in driver.current_url:
                driver.get(GRADE_URL)
                time.sleep(3)
                
            tables = driver.find_elements(By.TAG_NAME, "table")
            for table in tables:
                if "课程名称" in table.text:
                    rows = table.find_elements(By.TAG_NAME, "tr")
                    for row in rows:
                        cols = row.find_elements(By.TAG_NAME, "td")
                        # ✨ 修改点：这里改为 6，因为绩点在第 6 列 (索引5)
                        if len(cols) >= 6:
                            name = cols[2].text.strip()
                            grade_txt = cols[4].text.strip()
                            gpa_txt = cols[5].text.strip() # 抓取绩点列
                            
                            # ✨ 修改点：将成绩和绩点拼接显示，例如 "A | 4.0"
                            if name != "课程名称" and name and grade_txt:
                                # 如果绩点是 -- (比如P通过)，就只显示成绩，否则显示 成绩 | 绩点
                                if gpa_txt and gpa_txt != "--":
                                    final_value = f"{grade_txt} | {gpa_txt}"
                                else:
                                    final_value = grade_txt
                                    
                                data["grades"][name] = final_value
                    break
            
            # 3. 抓总GPA
            driver.get(GPA_URL)
            try:
                wait.until(EC.presence_of_element_located((By.ID, "my-gpa")))
                data["gpa"] = driver.find_element(By.ID, "my-gpa").text.strip()
                data["rank"] = driver.find_element(By.ID, "my-ranking").text.strip()
                self.log(f"✅ 数据刷新: {len(data['grades'])}门课 | GPA:{data['gpa']} | Rank:{data['rank']}", level=1)
            except:
                self.log("⚠️ 暂未获取到总GPA数据", level=2)

            return data

        except Exception as e:
            self.log(f"❌ 致命错误: {str(e)[:30]}", level=1)
            return None
        finally:
            if driver: driver.quit()

    def handle_data(self, current_data, token):
        old_data = self.load_history()
        is_updated, msg = self.compare_data(current_data, old_data)
        
        self.save_history(current_data)
        
        # 刷新UI
        self.root.after(0, self.refresh_dashboard_from_file)
        
        if is_updated:
            self.log("🎉 发现更新！正在推送...", level=1)
            if "第一次" not in msg and token:
                self.send_wechat(token, "复旦成绩单更新", msg)
            elif not token:
                self.log("未配置Token，跳过推送", level=2)
        else:
            # 如果没有更新，这一行就足够了，不需要废话
            self.log("👌 暂无成绩变动", level=1)

    def compare_data(self, new, old):
        if not old: return True, "这是第一次运行，建立基准数据"
        updates = []
        if new['gpa'] != old.get('gpa'): updates.append(f"🔴 GPA变动: {old.get('gpa')} -> {new['gpa']}")
        if new['rank'] != old.get('rank'): updates.append(f"🔴 排名变动: {old.get('rank')} -> {new['rank']}")
        
        new_grades = new.get('grades', {})
        old_grades = old.get('grades', {})
        for c, g in new_grades.items():
            if c not in old_grades: updates.append(f"🟢 新出分: {c} {g}")
            elif old_grades[c] != g: updates.append(f"🟡 分数变动: {c} {old_grades[c]} -> {g}")
            
        if updates:
            return True, "<br>".join(updates) + f"<br><br>📊 GPA: {new['gpa']} | Rank: {new['rank']}"
        return False, ""

    def load_history(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, 'r', encoding='utf-8') as f: return json.load(f)
            except: pass
        return None

    def save_history(self, data):
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def send_wechat(self, token, title, content):
        url = "http://www.pushplus.plus/send"
        data = {"token": token, "title": title, "content": content, "template": "html"}
        try:
            requests.post(url, json=data)
            self.log("✅ 微信推送成功！")
        except Exception as e:
            self.log(f"❌ 微信推送失败: {e}")

    def refresh_dashboard_from_file(self):
        """刷新成绩单Tab显示"""
        data = self.load_history()
        if not data: return
        
        try:
            self.lbl_gpa.config(text=f"🏆 总GPA: {data.get('gpa', '--')}")
            self.lbl_rank.config(text=f"🥇 专业排名: {data.get('rank', '--')}")
            
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            grades = data.get("grades", {})
            for course, grade in grades.items():
                self.tree.insert("", "end", values=(course, grade))
        except Exception as e:
            print(f"UI刷新错误: {e}")

if __name__ == "__main__":
    # 确保依赖已安装
    # pip install requests selenium webdriver_manager
    root = tk.Tk()
    app = GradeMonitorApp(root)
    root.mainloop()