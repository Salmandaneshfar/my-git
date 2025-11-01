import os
import sys
import json
import threading
import subprocess
import webbrowser
import secrets
from datetime import datetime
from pathlib import Path
from tkinter import (
    Tk, ttk, Label, Entry, Button, Checkbutton, BooleanVar, StringVar,
    Text, Scrollbar, messagebox, filedialog, Frame, Spinbox, DoubleVar, IntVar,
    Toplevel, Listbox
)
from tkcalendar import DateEntry

# Import functions from commiter.py
from commiter import create_commit, generate_dates
from git import Repo
import random

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

class GitCommiterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Git Commiter - رابط گرافیکی")
        self.root.geometry("900x750")
        self.root.resizable(True, True)
        
        # Store repositories and their configs
        self.repositories = {}  # {repo_name: repo_path}
        self.configs_file = "repositories_config.json"
        self.github_credentials_file = "github_credentials.json"
        
        # Load saved repositories and credentials
        self.load_repositories()
        self.load_github_credentials()
        
        self.create_widgets()
        self.setup_layout()
        
    def create_widgets(self):
        # Main container with padding
        main_frame = Frame(self.root, padx=10, pady=10)
        main_frame.pack(fill='both', expand=True)
        
        # Title
        title_label = Label(main_frame, text="🤖 Git Commiter - سازنده خودکار Commit", 
                          font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Repository Section
        repo_frame = Label(main_frame, text="📁 Repository", font=('Arial', 12, 'bold'))
        repo_frame.pack(anchor='w', pady=(0, 5))
        
        repo_container = Frame(main_frame, relief='sunken', borderwidth=1, padx=5, pady=5)
        repo_container.pack(fill='x', pady=(0, 15))
        
        self.repo_var = ttk.Combobox(repo_container, width=50, state='readonly')
        self.repo_var.pack(side='left', padx=5, pady=5)
        self.repo_var.bind('<<ComboboxSelected>>', self.on_repo_selected)
        
        Button(repo_container, text="➕ افزودن", command=self.add_repository).pack(side='left', padx=5)
        Button(repo_container, text="🐙 از GitHub", command=self.load_from_github).pack(side='left', padx=5)
        Button(repo_container, text="🗑️ حذف", command=self.remove_repository).pack(side='left', padx=5)
        Button(repo_container, text="🔄 به‌روزرسانی", command=self.refresh_repo_info).pack(side='left', padx=5)
        
        # Repository info label
        self.repo_info_label = Label(main_frame, text="", fg='gray', font=('Arial', 9))
        self.repo_info_label.pack(anchor='w', pady=(0, 15))
        
        # Date Range Section
        date_frame = Label(main_frame, text="📅 بازه زمانی", font=('Arial', 12, 'bold'))
        date_frame.pack(anchor='w', pady=(0, 5))
        
        date_container = Frame(main_frame)
        date_container.pack(fill='x', pady=(0, 15))
        
        Label(date_container, text="از تاریخ:").pack(side='left', padx=5)
        self.start_date = DateEntry(date_container, width=12, background='darkblue',
                                    foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        self.start_date.pack(side='left', padx=5)
        
        Label(date_container, text="تا تاریخ:").pack(side='left', padx=5)
        self.end_date = DateEntry(date_container, width=12, background='darkblue',
                                  foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        self.end_date.pack(side='left', padx=5)
        
        # Commit Settings Section
        settings_frame = Label(main_frame, text="⚙️ تنظیمات Commit", font=('Arial', 12, 'bold'))
        settings_frame.pack(anchor='w', pady=(0, 5))
        
        settings_container = Frame(main_frame, relief='sunken', borderwidth=1, padx=5, pady=5)
        settings_container.pack(fill='x', pady=(0, 15))
        
        # Skip probability
        skip_frame = Frame(settings_container)
        skip_frame.pack(fill='x', pady=5)
        Label(skip_frame, text="احتمال skip روز:").pack(side='left', padx=5)
        self.skip_prob_var = DoubleVar(value=0.2)
        Spinbox(skip_frame, from_=0.0, to=1.0, increment=0.1, width=10, 
                textvariable=self.skip_prob_var, format="%.1f").pack(side='left', padx=5)
        Label(skip_frame, text="(0.0 - 1.0)").pack(side='left', padx=5)
        
        # Min/Max commits
        commits_frame = Frame(settings_container)
        commits_frame.pack(fill='x', pady=5)
        Label(commits_frame, text="حداقل commit:").pack(side='left', padx=5)
        self.min_commits_var = IntVar(value=1)
        Spinbox(commits_frame, from_=1, to=20, width=10, 
                textvariable=self.min_commits_var).pack(side='left', padx=5)
        
        Label(commits_frame, text="حداکثر commit:").pack(side='left', padx=5)
        self.max_commits_var = IntVar(value=6)
        Spinbox(commits_frame, from_=1, to=20, width=10, 
                textvariable=self.max_commits_var).pack(side='left', padx=5)
        
        # Options
        options_frame = Frame(main_frame)
        options_frame.pack(fill='x', pady=(0, 15))
        
        self.auto_push_var = BooleanVar(value=True)  # Default: True - always push to GitHub
        push_check = Checkbutton(options_frame, text="✅ Push خودکار به GitHub (پیشنهادی)", 
                   variable=self.auto_push_var)
        push_check.pack(side='left', padx=10)
        
        # Tooltip-like label
        Label(options_frame, text="💡 توصیه: فعال باشد تا commit ها در GitHub نمایش داده شوند",
              font=('Arial', 8), fg='green').pack(side='left', padx=5)
        
        self.dry_run_var = BooleanVar(value=False)
        Checkbutton(options_frame, text="Dry Run (تست بدون commit)", 
                   variable=self.dry_run_var).pack(side='left', padx=10)
        
        # Control Buttons
        buttons_frame = Frame(main_frame)
        buttons_frame.pack(fill='x', pady=(0, 10))
        
        Button(buttons_frame, text="▶️ شروع ساخت Commit", command=self.start_commits,
              bg='#4CAF50', fg='white', font=('Arial', 11, 'bold'), 
              padx=20, pady=5).pack(side='left', padx=5)
        
        Button(buttons_frame, text="⏹️ توقف", command=self.stop_commits,
              bg='#f44336', fg='white', font=('Arial', 11, 'bold'),
              padx=20, pady=5).pack(side='left', padx=5)
        
        Button(buttons_frame, text="💾 ذخیره تنظیمات", command=self.save_config,
              bg='#2196F3', fg='white', padx=20, pady=5).pack(side='left', padx=5)
        
        Button(buttons_frame, text="📥 بارگذاری تنظیمات", command=self.load_config,
              bg='#FF9800', fg='white', padx=20, pady=5).pack(side='left', padx=5)
        
        # Progress and Log Section
        log_frame = Label(main_frame, text="📋 لاگ و پیشرفت", font=('Arial', 12, 'bold'))
        log_frame.pack(anchor='w', pady=(10, 5))
        
        log_container = Frame(main_frame)
        log_container.pack(fill='both', expand=True)
        
        # Scrollbar for log
        scrollbar = Scrollbar(log_container)
        scrollbar.pack(side='right', fill='y')
        
        self.log_text = Text(log_container, height=12, wrap='word', yscrollcommand=scrollbar.set)
        self.log_text.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.log_text.yview)
        
        # Status bar
        self.status_var = StringVar(value="آماده - یک repository انتخاب کنید")
        status_bar = Label(main_frame, textvariable=self.status_var, 
                         relief='sunken', anchor='w', bg='#E0E0E0')
        status_bar.pack(fill='x', pady=(5, 0))
        
        # Thread control
        self.is_running = False
        self.stop_flag = False
        
        # Update repository list
        self.update_repo_list()
        
    def setup_layout(self):
        """Setup additional layout configurations"""
        # Set default dates
        today = datetime.now()
        self.start_date.set_date(today.replace(month=1, day=1))
        self.end_date.set_date(today)
        
    def log_message(self, message, color='black'):
        """Add message to log text area"""
        self.log_text.insert('end', f"{message}\n")
        self.log_text.see('end')
        self.root.update_idletasks()
        
    def update_repo_list(self):
        """Update the repository combobox"""
        repo_list = []
        for name, path in self.repositories.items():
            if name.startswith("GitHub:"):
                # Format GitHub repos nicely
                display_name = f"🐙 {name.replace('GitHub:', '')} (GitHub Direct)"
            else:
                # Format local repos
                display_name = f"{name} ({path})"
            repo_list.append(f"{display_name}")
        self.repo_var['values'] = repo_list
        if repo_list:
            self.repo_var.current(0)
            self.on_repo_selected()
    
    def add_repository(self):
        """Add a new repository"""
        repo_path = filedialog.askdirectory(title="انتخاب پوشه Repository")
        if repo_path:
            repo_path = Path(repo_path).resolve()
            repo_name = repo_path.name
            
            # Check if it's a git repo
            git_dir = repo_path / '.git'
            if not git_dir.exists():
                if messagebox.askyesno("تایید", 
                    f"این پوشه repository Git نیست.\nآیا می‌خواهید یک repository جدید ایجاد کنید؟"):
                    try:
                        Repo.init(repo_path)
                        messagebox.showinfo("موفق", f"Repository جدید در {repo_path} ایجاد شد")
                    except Exception as e:
                        messagebox.showerror("خطا", f"خطا در ایجاد repository: {e}")
                        return
                else:
                    return
            
            # Add to repositories
            if repo_name not in self.repositories:
                self.repositories[repo_name] = str(repo_path)
                self.save_repositories()
                self.update_repo_list()
                self.log_message(f"✅ Repository '{repo_name}' افزوده شد: {repo_path}")
                messagebox.showinfo("موفق", f"Repository '{repo_name}' افزوده شد")
            else:
                messagebox.showwarning("هشدار", f"Repository '{repo_name}' قبلاً اضافه شده است")
    
    def remove_repository(self):
        """Remove selected repository"""
        selected = self.repo_var.get()
        if not selected:
            messagebox.showwarning("هشدار", "لطفاً یک repository انتخاب کنید")
            return
        
        repo_name = selected.split(' (')[0]
        if messagebox.askyesno("تایید", f"آیا می‌خواهید '{repo_name}' را حذف کنید؟"):
            del self.repositories[repo_name]
            self.save_repositories()
            self.update_repo_list()
            self.repo_info_label.config(text="")
            self.log_message(f"🗑️ Repository '{repo_name}' حذف شد")
    
    def refresh_repo_info(self):
        """Refresh repository information"""
        self.on_repo_selected()
    
    def load_from_github(self):
        """Load repositories from GitHub"""
        if not HAS_REQUESTS:
            messagebox.showerror("خطا", 
                "کتابخانه 'requests' نصب نیست.\nلطفاً با دستور زیر نصب کنید:\npip install requests")
            return
        
        # Create window for GitHub login
        github_window = Toplevel(self.root)
        github_window.title("دریافت Repository ها از GitHub")
        github_window.geometry("600x600")
        github_window.transient(self.root)
        github_window.grab_set()
        
        main_frame = Frame(github_window, padx=20, pady=20)
        main_frame.pack(fill='both', expand=True)
        
        # Load saved credentials first
        saved_username = self.github_credentials.get('username', '')
        saved_token = self.github_credentials.get('token', '')
        saved_email = self.github_credentials.get('email', '')
        
        # Warning if token looks like password
        if saved_token and '@' in saved_token and len(saved_token) < 20:
            # Looks like password or invalid token
            saved_token = ""
            messagebox.showwarning("هشدار", 
                "⚠️ Token ذخیره شده نامعتبر به نظر می‌رسد.\n\n"
                "لطفاً یک Personal Access Token معتبر از GitHub بسازید:\n"
                "1. دکمه '🔐 دریافت Token از GitHub' را بزنید\n"
                "2. در GitHub یک Token جدید بسازید\n"
                "3. Token را کپی و وارد کنید")
        
        # Header
        header_frame = Frame(main_frame)
        header_frame.pack(fill='x', pady=(0, 10))
        
        Label(header_frame, text="🔐 GitHub اتصال", font=('Arial', 12, 'bold')).pack(side='left')
        
        connection_status = Label(header_frame, text="❌ متصل نیست", fg='red', font=('Arial', 9))
        connection_status.pack(side='left', padx=(10, 0))
        
        # Email (optional - for reference)
        Label(main_frame, text="📧 Email (اختیاری - برای یادآوری):").pack(anchor='w', pady=(10, 5))
        email_var = StringVar(value=saved_email)
        Entry(main_frame, textvariable=email_var, width=40).pack(fill='x', pady=(0, 5))
        Label(main_frame, text="💡 این فیلد فقط برای یادآوری است. از Username برای دریافت Repository استفاده می‌شود.",
              font=('Arial', 7), fg='gray', justify='left').pack(anchor='w', pady=(0, 10))
        
        # Username
        Label(main_frame, text="🔑 Username یا Organization GitHub:").pack(anchor='w', pady=(10, 5))
        username_var = StringVar(value=saved_username if saved_username else "salmandaneshfar")
        Entry(main_frame, textvariable=username_var, width=40).pack(fill='x', pady=(0, 10))
        
        # Token (optional but recommended)
        Label(main_frame, text="GitHub Personal Access Token (برای private repos ضروری):").pack(anchor='w', pady=(10, 5))
        token_var = StringVar(value=saved_token)
        token_entry = Entry(main_frame, textvariable=token_var, width=40, show='*')
        token_entry.pack(fill='x', pady=(0, 5))
        
        def update_connection_status():
            """Update connection status indicator"""
            try:
                username = username_var.get().strip()
                token = token_var.get().strip()
                
                if username and token:
                    # Validate token format (GitHub tokens are typically 40+ chars and don't contain @)
                    if len(token) < 20 or ('@' in token and len(token) < 40):
                        connection_status.config(text="⚠️ Token نامعتبر - نیاز به Personal Access Token", fg='orange')
                    else:
                        connection_status.config(text="✅ آماده اتصال", fg='green')
                elif username:
                    connection_status.config(text="⚠️ Token نیاز است", fg='orange')
                else:
                    connection_status.config(text="❌ متصل نیست", fg='red')
            except:
                pass
        
        # Auto-fetch when both username and token are filled
        auto_fetch_enabled = BooleanVar(value=True)
        
        def try_auto_fetch():
            """Auto fetch repos when username and token are both filled"""
            try:
                if not auto_fetch_enabled.get():
                    return
                    
                username = username_var.get().strip()
                token = token_var.get().strip()
                
                if username and token:
                    # Wait a bit to make sure user finished typing
                    github_window.after(1500, lambda: fetch_repos())
            except:
                pass
        
        # Update on change
        username_var.trace('w', lambda *args: update_connection_status())
        token_var.trace('w', lambda *args: update_connection_status())
        update_connection_status()
        
        # Auto-fetch checkbox
        Checkbutton(main_frame, text="🔄 دریافت خودکار Repository ها (وقتی Username و Token وارد شدند)",
                   variable=auto_fetch_enabled, font=('Arial', 8)).pack(anchor='w', pady=(0, 10))
        
        # Monitor changes for auto-fetch
        username_var.trace('w', lambda *args: github_window.after(2000, try_auto_fetch))
        token_var.trace('w', lambda *args: github_window.after(2000, try_auto_fetch))
        
        def save_credentials():
            """Save credentials to file"""
            creds = {
                'username': username_var.get().strip(),
                'token': token_var.get().strip(),
                'email': email_var.get().strip()
            }
            with open(self.github_credentials_file, 'w', encoding='utf-8') as f:
                json.dump(creds, f, indent=2)
            self.github_credentials = creds
            messagebox.showinfo("موفق", "اطلاعات ذخیره شد")
        
        oauth_frame = Frame(main_frame)
        oauth_frame.pack(fill='x', pady=(0, 10))
        
        def open_github_token_page():
            """Open GitHub token creation page in browser"""
            # Open GitHub login page first (in case not logged in)
            login_url = 'https://github.com/login'
            webbrowser.open(login_url)
            
            # Then open token creation page after a delay
            import time
            time.sleep(1)
            webbrowser.open('https://github.com/settings/tokens/new')
            
            messagebox.showinfo("GitHub OAuth", 
                "صفحات GitHub در browser باز شدند.\n\n"
                "📋 مراحل:\n"
                "1. اگر لاگین نیستید، ابتدا با GitHub لاگین کنید\n"
                "2. سپس صفحه Token باز می‌شود\n"
                "3. نامی برای token انتخاب کنید (مثلاً: Git Commiter)\n"
                "4. دسترسی 'repo' را انتخاب کنید\n"
                "5. Generate token را بزنید\n"
                "6. Token را کپی کنید و در فیلد Token بالا وارد کنید\n"
                "7. دکمه '💾 ذخیره اطلاعات' را بزنید")
        
        def check_github_cli():
            """Check if GitHub CLI (gh) is installed"""
            try:
                result = subprocess.run(['gh', '--version'], 
                                      capture_output=True, timeout=5)
                if result.returncode == 0:
                    # gh CLI is installed - try to get token
                    try:
                        result = subprocess.run(['gh', 'auth', 'token'], 
                                              capture_output=True, timeout=5)
                        if result.returncode == 0:
                            token = result.stdout.decode().strip()
                            if token:
                                token_var.set(token)
                                messagebox.showinfo("موفق", 
                                    "✅ Token از GitHub CLI دریافت شد!\n\n"
                                    "Token در فیلد Token وارد شد.\n"
                                    "لطفاً دکمه '💾 ذخیره اطلاعات' را بزنید.")
                                return True
                    except:
                        pass
                    
                    # Try to login
                    messagebox.showinfo("GitHub CLI", 
                        "GitHub CLI (gh) نصب است.\n\n"
                        "لطفاً در terminal اجرا کنید:\n"
                        "  gh auth login\n\n"
                        "یا از دکمه بالا برای دریافت Token استفاده کنید.")
                else:
                    messagebox.showinfo("GitHub CLI", 
                        "GitHub CLI (gh) نصب نیست.\n\n"
                        "می‌توانید نصب کنید از:\n"
                        "  https://cli.github.com/\n\n"
                        "یا از دکمه بالا برای دریافت Token استفاده کنید.")
            except FileNotFoundError:
                messagebox.showinfo("GitHub CLI", 
                    "GitHub CLI (gh) نصب نیست.\n\n"
                    "می‌توانید نصب کنید از:\n"
                    "  https://cli.github.com/\n\n"
                    "یا از دکمه بالا برای دریافت Token استفاده کنید.")
            return False
        
        Button(oauth_frame, text="🔐 دریافت Token از GitHub", command=open_github_token_page,
              bg='#2196F3', fg='white', font=('Arial', 9), padx=15, pady=5).pack(side='left', padx=(0, 5))
        
        Button(oauth_frame, text="🔍 بررسی GitHub CLI", command=check_github_cli,
              bg='#9C27B0', fg='white', font=('Arial', 9), padx=15, pady=5).pack(side='left', padx=(0, 5))
        
        Button(main_frame, text="💾 ذخیره اطلاعات", command=save_credentials,
              bg='#FF9800', fg='white', font=('Arial', 9)).pack(anchor='w', pady=(0, 5))
        
        Label(main_frame, text="💡 می‌توانید:\n"
              "   🔐 از دکمه بالا استفاده کنید تا صفحه GitHub باز شود\n"
              "   📝 یا دستی token را از GitHub > Settings > Developer settings > Personal access tokens بسازید\n"
              "⚠️ GitHub دیگر password قبول نمی‌کند - فقط Personal Access Token",
              font=('Arial', 8), fg='gray', justify='left').pack(anchor='w', pady=(0, 10))
        
        # Clone directory
        Label(main_frame, text="پوشه Clone (اختیاری):").pack(anchor='w', pady=(10, 5))
        clone_dir_var = StringVar()
        clone_frame = Frame(main_frame)
        clone_frame.pack(fill='x', pady=(0, 10))
        Entry(clone_frame, textvariable=clone_dir_var, width=30).pack(side='left', padx=(0, 5))
        Button(clone_frame, text="انتخاب", command=lambda: clone_dir_var.set(filedialog.askdirectory())).pack(side='left')
        
        # Repositories list
        Label(main_frame, text="Repository ها:", font=('Arial', 10, 'bold')).pack(anchor='w', pady=(10, 5))
        
        list_frame = Frame(main_frame)
        list_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        scrollbar = Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')
        
        repo_listbox = Listbox(list_frame, yscrollcommand=scrollbar.set, selectmode='multiple')
        repo_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=repo_listbox.yview)
        
        status_label = Label(main_frame, text="", fg='gray', font=('Arial', 9))
        status_label.pack(pady=(0, 10))
        
        def fetch_repos():
            """Fetch repositories from GitHub"""
            username = username_var.get().strip()
            token = token_var.get().strip()
            
            if not username:
                messagebox.showerror("خطا", "لطفاً Username یا Organization را وارد کنید")
                return
            
            status_label.config(text="در حال دریافت repository ها...", fg='blue')
            github_window.update()
            
            try:
                headers = {
                    'Accept': 'application/vnd.github.v3+json',
                    'User-Agent': 'Git-Commiter-App'
                }
                if token:
                    headers['Authorization'] = f'token {token}'
                    # Check if token owner matches requested username
                    try:
                        response_test = requests.get('https://api.github.com/user', headers=headers, timeout=5)
                        if response_test.ok:
                            token_owner = response_test.json().get('login', '').lower()
                            if token_owner == username.lower():
                                # Token owner matches requested username - get all repos (including private)
                                url = 'https://api.github.com/user/repos'
                                params = {'per_page': 100, 'type': 'all', 'affiliation': 'owner'}
                            else:
                                # Token owner is different - use public API for that username
                                url = f'https://api.github.com/users/{username}/repos'
                                params = {'per_page': 100, 'type': 'all'}
                        else:
                            # Can't verify token owner, use public API
                            url = f'https://api.github.com/users/{username}/repos'
                            params = {'per_page': 100, 'type': 'all'}
                    except:
                        # Error checking token, use public API
                        url = f'https://api.github.com/users/{username}/repos'
                        params = {'per_page': 100, 'type': 'all'}
                else:
                    # Without token, only public repos
                    url = f'https://api.github.com/users/{username}/repos'
                    params = {'per_page': 100, 'type': 'all'}
                
                status_label.config(text=f"در حال دریافت repository های {username}...", fg='blue')
                github_window.update()
                
                response = requests.get(url, headers=headers, params=params, timeout=15)
                
                # Check for errors
                if response.status_code == 404:
                    status_label.config(text=f"❌ User '{username}' یافت نشد", fg='red')
                    messagebox.showerror("خطا", f"User یا Organization '{username}' یافت نشد")
                    return
                elif response.status_code == 403:
                    status_label.config(text="❌ محدودیت rate limit - لطفاً صبر کنید", fg='red')
                    messagebox.showerror("خطا", "GitHub rate limit رسیده. لطفاً چند دقیقه صبر کنید.")
                    return
                
                response.raise_for_status()
                
                repos = response.json()
                
                # Debug: log what we got
                print(f"\n🔍 DEBUG Info:")
                print(f"   URL: {url}")
                print(f"   Status: {response.status_code}")
                print(f"   Repositories found: {len(repos)}")
                if repos:
                    print(f"   First repo: {repos[0].get('name', 'N/A')}")
                    print(f"   Sample repos: {[r.get('name') for r in repos[:3]]}")
                print()
                
                if not repos or len(repos) == 0:
                    status_label.config(text="❌ هیچ repository ای یافت نشد", fg='orange')
                    github_window.update()
                    
                    # Clear the listbox to show empty state
                    repo_listbox.delete(0, 'end')
                    repo_listbox.insert(0, "⚠️ هیچ repository ای یافت نشد")
                    
                    # Check if user exists and provide helpful message
                    try:
                        user_check = requests.get(f'https://api.github.com/users/{username}', 
                                                headers=headers, timeout=5)
                        if user_check.status_code == 200:
                            user_data = user_check.json()
                            public_repos = user_data.get('public_repos', 0)
                            
                            print(f"DEBUG: User exists - Public repos: {public_repos}")
                            
                            if public_repos == 0:
                                # No public repos - show helpful message
                                status_label.config(
                                    text=f"✅ User '{username}' یافت شد | Public Repos: 0 | برای Private Repos باید Token وارد کنید", 
                                    fg='orange'
                                )
                                
                                # Add helpful info to listbox
                                repo_listbox.delete(0, 'end')
                                repo_listbox.insert(0, f"✅ User '{username}' یافت شد")
                                repo_listbox.insert(1, "⚠️ هیچ Repository Public یافت نشد")
                                repo_listbox.insert(2, "")
                                repo_listbox.insert(3, "💡 راه حل:")
                                repo_listbox.insert(4, "   1. اگر Private Repository دارید:")
                                repo_listbox.insert(5, "      → Personal Access Token بسازید")
                                repo_listbox.insert(6, "      → Token را در فیلد Token وارد کنید")
                                repo_listbox.insert(7, "   2. یا یک Public Repository بسازید")
                                
                                msg = (
                                    f"✅ User '{username}' یافت شد اما هیچ Repository Public ندارد.\n\n"
                                    f"📋 تعداد Repository های Public: 0\n\n"
                                    f"💡 راه حل‌ها:\n"
                                    f"   🔐 اگر Repository های Private دارید:\n"
                                    f"      1. Personal Access Token بسازید\n"
                                    f"      2. Token را در فیلد Token وارد کنید\n"
                                    f"      3. دوباره امتحان کنید\n\n"
                                    f"   🌐 یا یک Repository Public بسازید در GitHub"
                                )
                            else:
                                # Has public repos but didn't get them - API issue
                                status_label.config(
                                    text=f"⚠️ {public_repos} repository public یافت شد اما نمایش داده نشد", 
                                    fg='orange'
                                )
                                msg = (
                                    f"⚠️ {public_repos} repository public برای '{username}' یافت شد\n"
                                    f"اما با این request نمایش داده نشد.\n\n"
                                    f"💡 لطفاً:\n"
                                    f"   1. دوباره امتحان کنید\n"
                                    f"   2. Token را وارد کنید\n"
                                    f"   3. اتصال اینترنت را بررسی کنید"
                                )
                        else:
                            status_label.config(text=f"❌ User '{username}' یافت نشد", fg='red')
                            msg = (
                                f"❌ User یا Organization '{username}' یافت نشد.\n\n"
                                f"💡 لطفاً:\n"
                                f"   - Username را بررسی کنید\n"
                                f"   - مطمئن شوید که username درست است\n"
                                f"   - Organization name را وارد کنید (اگر organization است)"
                            )
                    except Exception as e:
                        status_label.config(text=f"❌ خطا در بررسی User: {e}", fg='red')
                        msg = (
                            f"❌ خطا در دریافت اطلاعات:\n{str(e)}\n\n"
                            f"💡 لطفاً:\n"
                            f"   - اتصال اینترنت را بررسی کنید\n"
                            f"   - دوباره امتحان کنید"
                        )
                        print(f"DEBUG: Error checking user: {e}")
                    
                    github_window.update()
                    messagebox.showinfo("اطلاع", msg)
                    return
                
                # Clear and populate list
                repo_listbox.delete(0, 'end')
                repo_data = []
                
                # Filter repos by username if needed (when using /user/repos with token)
                filtered_repos = repos
                if token and url == 'https://api.github.com/user/repos':
                    # Filter to only repos owned by the requested username
                    filtered_repos = [r for r in repos if r.get('owner', {}).get('login', '').lower() == username.lower()]
                    if not filtered_repos:
                        # If no exact match, show all repos from token owner
                        filtered_repos = repos
                
                for repo in filtered_repos:
                    repo_name = repo['name']
                    repo_full_name = repo['full_name']
                    repo_url = repo['clone_url']
                    is_private = repo.get('private', False)
                    owner = repo.get('owner', {}).get('login', '')
                    
                    display_name = f"{repo_full_name} {'🔒 Private' if is_private else '🌐 Public'}"
                    repo_listbox.insert('end', display_name)
                    repo_data.append({
                        'name': repo_name,
                        'full_name': repo_full_name,
                        'url': repo_url,
                        'private': is_private,
                        'owner': owner
                    })
                
                status_label.config(text=f"✓ {len(filtered_repos)} repository یافت شد", fg='green')
                github_window.update()
                
                def select_and_close():
                    """Handle repository selection - Direct GitHub mode (no local clone needed)"""
                    selected_indices = repo_listbox.curselection()
                    if not selected_indices:
                        messagebox.showwarning("هشدار", "لطفاً حداقل یک repository انتخاب کنید")
                        return
                    
                    # Use temp directory for GitHub direct mode
                    temp_base = Path.home() / ".git_commiter_temp"
                    temp_base.mkdir(parents=True, exist_ok=True)
                    
                    for idx in selected_indices:
                        repo_info = repo_data[idx]
                        repo_name = repo_info['name']
                        repo_full_name = repo_info['full_name']
                        repo_url = repo_info['url']
                        
                        # Use repo full name to avoid conflicts
                        safe_repo_name = repo_full_name.replace('/', '_')
                        repo_path = temp_base / safe_repo_name
                        
                        try:
                            # Check if already cloned
                            if repo_path.exists() and (repo_path / '.git').exists():
                                # Update existing repo
                                status_label.config(text=f"به‌روزرسانی {repo_name}...", fg='blue')
                                github_window.update()
                                
                                try:
                                    repo = Repo(repo_path)
                                    repo.remotes.origin.fetch()
                                    self.log_message(f"✅ Repository موجود '{repo_full_name}' به‌روزرسانی شد")
                                except:
                                    # If update fails, clone again
                                    import shutil
                                    shutil.rmtree(repo_path, ignore_errors=True)
                                    raise
                            else:
                                # Clone repository
                                status_label.config(text=f"در حال clone کردن {repo_name}...", fg='blue')
                                github_window.update()
                                
                                # Prepare clone command with token if available
                                clone_cmd = ['git', 'clone', repo_url, str(repo_path)]
                                
                                # If token is available, use it for authentication
                                if token:
                                    # Modify URL to include token for private repos
                                    from urllib.parse import urlparse
                                    parsed = urlparse(repo_url)
                                    if repo_info['private']:
                                        # For private repos, use token in URL (HTTPS only)
                                        auth_url = f"https://{token}@{parsed.netloc}{parsed.path}"
                                        clone_cmd = ['git', 'clone', auth_url, str(repo_path)]
                                
                                subprocess.run(clone_cmd, check=True, capture_output=True, timeout=300)
                                self.log_message(f"✅ Repository '{repo_full_name}' clone شد")
                            
                            # Add to repositories list (stored as GitHub URL for direct mode)
                            repo_key = f"GitHub:{repo_full_name}"
                            self.repositories[repo_key] = str(repo_path.resolve())
                            self.log_message(f"📦 Repository '{repo_full_name}' آماده برای استفاده مستقیم از GitHub")
                            
                        except subprocess.CalledProcessError as e:
                            error_msg = e.stderr.decode() if e.stderr else str(e)
                            self.log_message(f"❌ خطا در clone کردن '{repo_full_name}': {error_msg}")
                            messagebox.showerror("خطا", 
                                f"خطا در clone کردن '{repo_full_name}':\n{error_msg}\n\n"
                                f"💡 برای Private Repository ها، لطفاً Token را وارد کنید.")
                        except Exception as e:
                            self.log_message(f"❌ خطا در clone کردن '{repo_full_name}': {e}")
                            messagebox.showerror("خطا", f"خطا در clone کردن '{repo_full_name}': {e}")
                    
                    self.save_repositories()
                    self.update_repo_list()
                    github_window.destroy()
                    messagebox.showinfo("موفق", 
                        f"{len(selected_indices)} repository افزوده شد!\n\n"
                        f"💡 Repository ها در حالت 'GitHub Direct' هستند:\n"
                        f"   - Commit ها مستقیماً به GitHub push می‌شوند\n"
                        f"   - Repository در {temp_base} نگه‌داری می‌شود\n"
                        f"   - بعد از هر بار استفاده، به‌روزرسانی می‌شود")
                
                buttons_frame = Frame(main_frame)
                buttons_frame.pack(fill='x', pady=(10, 0))
                
                Button(buttons_frame, text="✅ انتخاب و افزودن", command=select_and_close,
                      bg='#4CAF50', fg='white', font=('Arial', 10, 'bold'),
                      padx=20, pady=5).pack(side='left', padx=(0, 5))
                
                def add_local_repo():
                    """Add local repository as alternative"""
                    local_repo = filedialog.askdirectory(title="انتخاب Repository محلی")
                    if local_repo:
                        local_path = Path(local_repo).resolve()
                        git_dir = local_path / '.git'
                        if git_dir.exists():
                            repo_name = local_path.name
                            # Add as regular local repo
                            if repo_name not in self.repositories:
                                self.repositories[repo_name] = str(local_path)
                                self.save_repositories()
                                self.update_repo_list()
                                github_window.destroy()
                                messagebox.showinfo("موفق", 
                                    f"✅ Repository محلی '{repo_name}' افزوده شد!\n\n"
                                    f"می‌توانید از همین Repository برای ساخت Commit استفاده کنید.")
                            else:
                                messagebox.showwarning("هشدار", 
                                    f"Repository '{repo_name}' قبلاً اضافه شده است")
                        else:
                            messagebox.showerror("خطا", 
                                "این پوشه یک Repository Git نیست.\n"
                                "لطفاً یک پوشه با .git انتخاب کنید.")
                
                Button(buttons_frame, text="📁 افزودن Repository محلی", command=add_local_repo,
                      bg='#FF9800', fg='white', font=('Arial', 9),
                      padx=15, pady=5).pack(side='left', padx=(0, 5))
                
                Label(main_frame, text="💡 راهنمایی:\n"
                      "   - اگر هیچ Repository ای نمی‌بینید:\n"
                      "     1. Username را بررسی کنید\n"
                      "     2. Token وارد کنید (برای Private Repos)\n"
                      "     3. یا از Repository محلی استفاده کنید",
                      font=('Arial', 8), fg='blue', justify='left').pack(anchor='w', pady=(10, 0))
                
            except requests.exceptions.RequestException as e:
                status_label.config(text=f"❌ خطا: {e}", fg='red')
                messagebox.showerror("خطا", f"خطا در دریافت repository ها:\n{e}")
            except Exception as e:
                status_label.config(text=f"❌ خطا: {e}", fg='red')
                messagebox.showerror("خطا", f"خطای غیرمنتظره: {e}")
        
        # Auto-fetch button
        fetch_frame = Frame(main_frame)
        fetch_frame.pack(fill='x', pady=(10, 0))
        
        Button(fetch_frame, text="🔍 دریافت Repository ها", command=fetch_repos,
              bg='#2196F3', fg='white', font=('Arial', 10, 'bold'),
              padx=20, pady=5).pack(side='left', padx=(0, 5))
        
        def auto_fetch_and_select():
            """Auto fetch repos and add first one if only one exists"""
            username = username_var.get().strip()
            token = token_var.get().strip()
            
            if not username:
                messagebox.showerror("خطا", "لطفاً Username را وارد کنید")
                return
            
            # Auto fetch
            fetch_repos()
            
            # Wait a bit for repos to load, then auto-select if only one
            def check_and_select():
                github_window.update()
                try:
                    if repo_listbox.size() == 1:
                        # Only one repo - auto select
                        repo_listbox.selection_set(0)
                        select_and_close()
                    elif repo_listbox.size() > 1:
                        # Multiple repos - user selects
                        pass
                except:
                    pass
            
            github_window.after(1000, check_and_select)
        
        Button(fetch_frame, text="⚡ دریافت و استفاده خودکار", command=auto_fetch_and_select,
              bg='#4CAF50', fg='white', font=('Arial', 9, 'bold'),
              padx=15, pady=5).pack(side='left')
        
        Label(main_frame, text="💡 می‌توانید از 'دریافت و استفاده خودکار' استفاده کنید تا repository ها دریافت و افزوده شوند",
              font=('Arial', 8), fg='blue', justify='left').pack(anchor='w', pady=(5, 0))
    
    def on_repo_selected(self, event=None):
        """Called when repository is selected"""
        selected = self.repo_var.get()
        if not selected:
            return
        
        # Extract repo key from display name
        if selected.startswith("🐙 "):
            # GitHub repo: "🐙 user/repo (GitHub Direct)"
            repo_full_name = selected.replace("🐙 ", "").split(" (")[0]
            repo_key = f"GitHub:{repo_full_name}"
        else:
            # Local repo: "name (path)"
            repo_key = selected.split(' (')[0]
        
        repo_path = self.repositories.get(repo_key)
        
        if repo_path and Path(repo_path).exists():
            try:
                repo = Repo(repo_path)
                branch = repo.active_branch.name if not repo.bare else "N/A"
                
                if repo_key.startswith("GitHub:"):
                    repo_display = repo_key.replace("GitHub:", "")
                    self.repo_info_label.config(
                        text=f"🐙 GitHub Direct: {repo_display} | Branch: {branch}",
                        fg='blue'
                    )
                else:
                    self.repo_info_label.config(
                        text=f"📍 Branch: {branch} | Path: {repo_path}",
                        fg='green'
                    )
                
                # Load config for this repo (use safe name for config file)
                safe_name = repo_key.replace("GitHub:", "").replace("/", "_")
                self.load_repo_config(safe_name)
            except Exception as e:
                self.repo_info_label.config(text=f"❌ خطا: {e}", fg='red')
        else:
            self.repo_info_label.config(text="❌ Repository یافت نشد", fg='red')
    
    def get_selected_repo_path(self):
        """Get path of selected repository"""
        selected = self.repo_var.get()
        if not selected:
            return None
        
        # Extract repo key from display name
        if selected.startswith("🐙 "):
            # GitHub repo
            repo_full_name = selected.replace("🐙 ", "").split(" (")[0]
            repo_key = f"GitHub:{repo_full_name}"
        else:
            # Local repo
            repo_key = selected.split(' (')[0]
        
        return self.repositories.get(repo_key)
    
    def get_repo_config_file(self, repo_name):
        """Get config file path for a repository"""
        return f"config_{repo_name}.json"
    
    def save_repositories(self):
        """Save repositories list"""
        with open('repositories.json', 'w', encoding='utf-8') as f:
            json.dump(self.repositories, f, indent=2, ensure_ascii=False)
    
    def load_repositories(self):
        """Load repositories list"""
        if os.path.exists('repositories.json'):
            try:
                with open('repositories.json', 'r', encoding='utf-8') as f:
                    self.repositories = json.load(f)
            except:
                self.repositories = {}
    
    def load_github_credentials(self):
        """Load GitHub credentials"""
        self.github_credentials = {'username': '', 'token': '', 'email': ''}
        if os.path.exists(self.github_credentials_file):
            try:
                with open(self.github_credentials_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    self.github_credentials.update(loaded)
            except:
                pass
    
    def save_config(self):
        """Save current settings for selected repository"""
        repo_name = self.repo_var.get().split(' (')[0] if self.repo_var.get() else None
        if not repo_name:
            messagebox.showwarning("هشدار", "لطفاً یک repository انتخاب کنید")
            return
        
        config = {
            "start_date": self.start_date.get_date().strftime("%Y-%m-%d"),
            "end_date": self.end_date.get_date().strftime("%Y-%m-%d"),
            "skip_probability": self.skip_prob_var.get(),
            "min_commits": self.min_commits_var.get(),
            "max_commits": self.max_commits_var.get(),
            "auto_push": self.auto_push_var.get(),
            "repo_path": self.get_selected_repo_path()
        }
        
        config_file = self.get_repo_config_file(repo_name)
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        self.log_message(f"💾 تنظیمات برای '{repo_name}' ذخیره شد")
        messagebox.showinfo("موفق", f"تنظیمات در {config_file} ذخیره شد")
    
    def load_config(self):
        """Load saved config for selected repository"""
        repo_name = self.repo_var.get().split(' (')[0] if self.repo_var.get() else None
        if not repo_name:
            messagebox.showwarning("هشدار", "لطفاً یک repository انتخاب کنید")
            return
        
        self.load_repo_config(repo_name)
        messagebox.showinfo("موفق", f"تنظیمات برای '{repo_name}' بارگذاری شد")
    
    def load_repo_config(self, repo_name):
        """Load config for a repository"""
        config_file = self.get_repo_config_file(repo_name)
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # Update UI with loaded config
                if "start_date" in config:
                    self.start_date.set_date(datetime.strptime(config["start_date"], "%Y-%m-%d"))
                if "end_date" in config:
                    self.end_date.set_date(datetime.strptime(config["end_date"], "%Y-%m-%d"))
                if "skip_probability" in config:
                    self.skip_prob_var.set(config["skip_probability"])
                if "min_commits" in config:
                    self.min_commits_var.set(config["min_commits"])
                if "max_commits" in config:
                    self.max_commits_var.set(config["max_commits"])
                if "auto_push" in config:
                    self.auto_push_var.set(config["auto_push"])
                
                self.log_message(f"📥 تنظیمات برای '{repo_name}' بارگذاری شد")
            except Exception as e:
                self.log_message(f"⚠️ خطا در بارگذاری تنظیمات: {e}")
    
    def start_commits(self):
        """Start creating commits in a separate thread"""
        if self.is_running:
            messagebox.showwarning("هشدار", "فرآیند در حال اجرا است!")
            return
        
        repo_path = self.get_selected_repo_path()
        if not repo_path:
            messagebox.showerror("خطا", "لطفاً یک repository انتخاب کنید")
            return
        
        # Validate settings
        start_dt = self.start_date.get_date()
        end_dt = self.end_date.get_date()
        
        if start_dt > end_dt:
            messagebox.showerror("خطا", "تاریخ شروع باید قبل از تاریخ پایان باشد")
            return
        
        min_commits = self.min_commits_var.get()
        max_commits = self.max_commits_var.get()
        
        if min_commits > max_commits:
            messagebox.showerror("خطا", "حداقل commit نمی‌تواند بیشتر از حداکثر باشد")
            return
        
        # Start thread
        self.is_running = True
        self.stop_flag = False
        self.status_var.set("در حال اجرا...")
        
        thread = threading.Thread(target=self.create_commits_thread, 
                                 args=(repo_path, start_dt, end_dt), daemon=True)
        thread.start()
    
    def stop_commits(self):
        """Stop the commit creation process"""
        if self.is_running:
            self.stop_flag = True
            self.status_var.set("در حال توقف...")
            self.log_message("⏹️ درخواست توقف دریافت شد")
    
    def create_commits_thread(self, repo_path, start_dt, end_dt):
        """Thread function for creating commits"""
        try:
            # Check if this is a GitHub Direct repo
            is_github_direct = False
            repo_full_name = ""
            selected = self.repo_var.get()
            if selected and selected.startswith("🐙 "):
                is_github_direct = True
                repo_full_name = selected.replace("🐙 ", "").split(" (")[0]
                self.log_message(f"🐙 GitHub Direct Mode: {repo_full_name}")
            
            # For GitHub Direct repos, update first
            if is_github_direct:
                self.log_message(f"🔄 به‌روزرسانی repository از GitHub...")
                try:
                    repo = Repo(repo_path)
                    repo.remotes.origin.fetch()
                    repo.remotes.origin.pull()
                    self.log_message(f"✅ Repository به‌روزرسانی شد")
                except Exception as e:
                    self.log_message(f"⚠️ خطا در به‌روزرسانی: {e}")
            
            repo = Repo(repo_path)
            self.log_message(f"🚀 شروع ساخت commit برای: {repo_path}")
            
            skip_prob = self.skip_prob_var.get()
            min_commits = self.min_commits_var.get()
            max_commits = self.max_commits_var.get()
            auto_push = self.auto_push_var.get()
            dry_run = self.dry_run_var.get()
            
            total_commits = 0
            skipped_days = 0
            
            # Change to repo directory
            original_cwd = Path.cwd()
            os.chdir(repo_path)
            
            try:
                # Convert datetime.date to datetime.datetime
                start_date = datetime.combine(start_dt, datetime.min.time())
                end_date = datetime.combine(end_dt, datetime.min.time())
                
                for date_str in generate_dates(start_date, end_date):
                    if self.stop_flag:
                        self.log_message("⏹️ فرآیند متوقف شد")
                        break
                    
                    # Skip some days randomly
                    if random.random() < skip_prob:
                        self.log_message(f"⏭️ Skip: {date_str}")
                        skipped_days += 1
                        continue
                    
                    # Generate random number of commits
                    num_commits = random.randint(min_commits, max_commits)
                    self.log_message(f"📝 {date_str}: ساخت {num_commits} commit")
                    
                    if not dry_run:
                        for commit_number in range(1, num_commits + 1):
                            if self.stop_flag:
                                break
                            if create_commit(repo, date_str, commit_number):
                                total_commits += 1
                                self.log_message(f"  ✓ Commit {commit_number}/{num_commits}")
                            else:
                                self.log_message(f"  ✗ خطا در commit {commit_number}")
                    else:
                        total_commits += num_commits
                        self.log_message(f"  [DRY RUN] {num_commits} commit")
                
                self.log_message(f"\n📊 خلاصه:")
                self.log_message(f"  ✓ Total commits: {total_commits}")
                self.log_message(f"  ⏭️ Skipped days: {skipped_days}")
                
                # Push to GitHub - always push unless dry-run
                should_push = not dry_run and not self.stop_flag
                if should_push:
                    if auto_push or is_github_direct:
                        try:
                            self.log_message("📤 در حال push به GitHub...")
                            origin = repo.remote(name="origin")
                            
                            # Try to push - handle different scenarios
                            try:
                                origin.push()
                                self.log_message("✅ Push موفق بود - Commit ها در GitHub هستند! 🎉")
                                self.log_message(f"🌐 می‌توانید commit ها را در GitHub مشاهده کنید")
                                
                                if is_github_direct:
                                    self.log_message(f"🎉 Repository '{repo_full_name}' به‌روزرسانی شد")
                            except Exception as push_error:
                                # Check if it's authentication error
                                error_str = str(push_error).lower()
                                if 'authentication' in error_str or 'permission' in error_str or '403' in error_str:
                                    self.log_message("⚠️ خطا در احراز هویت برای push")
                                    self.log_message("💡 راه حل:")
                                    self.log_message("   1. مطمئن شوید remote URL درست است")
                                    self.log_message("   2. برای HTTPS: Token را در URL قرار دهید")
                                    self.log_message("   3. برای SSH: Key را بررسی کنید")
                                    self.log_message(f"   Remote URL: {origin.url}")
                                else:
                                    raise push_error
                        except Exception as e:
                            error_msg = str(e)
                            self.log_message(f"❌ خطا در push: {error_msg}")
                            self.log_message("💡 لطفاً:")
                            self.log_message("   1. اتصال اینترنت را بررسی کنید")
                            self.log_message("   2. دسترسی push را بررسی کنید")
                            self.log_message("   3. Remote repository را بررسی کنید")
                            
                            if is_github_direct:
                                self.log_message("💡 برای GitHub Direct، push ضروری است.")
                    else:
                        self.log_message("⚠️ Push خودکار غیرفعال است!")
                        self.log_message("💡 برای اعمال commit ها در GitHub، 'Push خودکار' را فعال کنید")
                        self.log_message("💡 یا دستی push کنید: git push")
                
            finally:
                os.chdir(original_cwd)
                
        except Exception as e:
            self.log_message(f"❌ خطا: {e}")
            import traceback
            self.log_message(traceback.format_exc())
        finally:
            self.is_running = False
            self.status_var.set("پایان یافت")
            if self.stop_flag:
                self.status_var.set("متوقف شد")

def main():
    root = Tk()
    app = GitCommiterGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()

