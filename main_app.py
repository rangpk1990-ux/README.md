import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import configparser
import threading
import time
import random
import webbrowser
from http_sender import HTTPSender

class App:
    def __init__(self, master):
        self.master = master
        master.title("API Tester (TH)")
        master.geometry("1000x800")
        
        # Initialize state variables
        self.config = self._load_config()
        self.tab_counter = 0
        self.request_data = {}  # Stores input widgets for each tab
        self.tab_response_body = {} # Stores response body area for each tab
        self.log_area = None # Text area for main log
        self.sender = HTTPSender()
        self.is_sending = False
        
        # State for status bar
        self.balance_var = tk.StringVar(value="0.00 บาท")
        self.bet_var = tk.StringVar(value="0")
        self.result_var = tk.StringVar(value="-")
        self.status_var = tk.StringVar(value="พร้อมทำงาน...")

        self._load_url_list()
        self._setup_ui()

    def _load_config(self):
        """Loads configuration from config.ini."""
        config = configparser.ConfigParser()
        try:
            config.read('config.ini')
            if 'DEFAULT_REQUEST' not in config:
                raise configparser.Error("Missing [DEFAULT_REQUEST] section.")
        except configparser.Error as e:
            messagebox.showerror("Configuration Error", f"Cannot load config.ini: {e}")
            # Use fallback defaults if config fails
            config['DEFAULT_REQUEST'] = {
                'DEFAULT_URL': 'https://jsonplaceholder.typicode.com/posts/1',
                'DEFAULT_METHOD': 'GET',
                'DEFAULT_PARAMS': 'userId: 1, limit: 3',
                'DEFAULT_HEADERS': 'Content-Type: application/json',
                'DEFAULT_PAYLOAD_JSON': '{"name": "Test User", "id": 1}'
            }
            config['EXECUTION'] = {'DEFAULT_REPEAT_COUNT': '5', 'REPEAT_DELAY_SECONDS': '1.0'}
            config['GENERAL'] = {'BET_ROUNDS': '2 cliker', 'BET_FINAL_ROUND': '1 cliker king&queen'}
        return config

    def _load_url_list(self):
        """Loads a list of URLs from linkgame.txt for initial tabs."""
        self.initial_urls = []
        try:
            with open('linkgame.txt', 'r', encoding='utf-8') as f:
                for line in f:
                    url = line.strip()
                    if url and not url.startswith('#'):
                        self.initial_urls.append(url)
        except FileNotFoundError:
            # If file not found, load one default tab
            self.initial_urls.append(self.config['DEFAULT_REQUEST']['DEFAULT_URL'])
        
        if not self.initial_urls:
            self.initial_urls.append(self.config['DEFAULT_REQUEST']['DEFAULT_URL'])

    def _setup_ui(self):
        """Sets up the main structure of the GUI."""
        
        # Main PanedWindow (Top/Bottom Split)
        main_paned = ttk.PanedWindow(self.master, orient=tk.VERTICAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- Top Frame: General Settings and Tabs ---
        top_frame = ttk.Frame(main_paned)
        top_frame.pack(fill='both', expand=True)
        
        # General Settings (Left side)
        general_frame = ttk.LabelFrame(top_frame, text="⚙️ General Settings", padding="10")
        general_frame.pack(side=tk.LEFT, fill='y', padx=10, pady=5)
        
        # Coin Selection Checkboxes
        coin_frame = ttk.LabelFrame(general_frame, text="🪙 เลือกเหรียญ (Coin Selection)")
        coin_frame.pack(pady=10, padx=5, fill='x')
        
        coin_options = [2, 10, 20, 50, 100, 500]
        self.coin_vars = {}
        for i, coin in enumerate(coin_options):
            var = tk.BooleanVar()
            self.coin_vars[coin] = var
            chk = ttk.Checkbutton(coin_frame, text=f"coin - {coin}", variable=var)
            chk.grid(row=i // 3, column=i % 3, padx=5, pady=2, sticky='w')
            
        # Other General Settings
        ttk.Label(general_frame, text="จำนวนรอบเดิมพัน:").pack(pady=(10, 0), padx=5, anchor='w')
        ttk.Label(general_frame, text=self.config['GENERAL']['BET_ROUNDS']).pack(padx=5, anchor='w')
        
        ttk.Label(general_frame, text="เงื่อนไขรอบสุดท้าย:").pack(pady=(10, 0), padx=5, anchor='w')
        ttk.Label(general_frame, text=self.config['GENERAL']['BET_FINAL_ROUND']).pack(padx=5, anchor='w')
        
        # Tabs (Notebook) (Right side)
        self.notebook = ttk.Notebook(top_frame)
        self.notebook.pack(side=tk.RIGHT, fill='both', expand=True, padx=10, pady=5)
        
        # Create initial tabs from loaded URLs
        for url in self.initial_urls:
            self._create_request_tab(f"ลำดับ", url=url)

        # Add buttons to the notebook for management
        button_frame = ttk.Frame(self.master)
        button_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(button_frame, text="➕ เพิ่มลำดับ", command=lambda: self._create_request_tab("ลำดับ")).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="❌ ลบลำดับปัจจุบัน", command=self._delete_current_tab).pack(side=tk.LEFT, padx=5)
        
        # --- Bottom Frame: Log and Status ---
        bottom_frame = ttk.Frame(main_paned)
        bottom_frame.pack(fill='both', expand=True)

        # Response Info Frame (Status Bar)
        response_info_frame = ttk.LabelFrame(bottom_frame, text="📊 สถานะและผลลัพธ์", padding="10")
        response_info_frame.pack(fill='x', padx=10, pady=5)
        
        # Layout for status information
        info_labels = [
            ("ยอดเงินคงเหลือ:", self.balance_var, 0),
            ("ยอดเดิมพัน:", self.bet_var, 2),
            ("ผลได้เสีย:", self.result_var, 4),
            ("สถานะ:", self.status_var, 6)
        ]

        for text, var, col in info_labels:
            ttk.Label(response_info_frame, text=text, font=('Inter', 10, 'bold')).grid(row=0, column=col, padx=5, pady=5, sticky='w')
            ttk.Label(response_info_frame, textvariable=var, font=('Inter', 10)).grid(row=0, column=col+1, padx=5, pady=5, sticky='w')
        
        response_info_frame.grid_columnconfigure(7, weight=1) # Push everything to the left

        # Main Log Area
        log_label = ttk.Label(bottom_frame, text="บันทึกผลลัพธ์ (Response Log):", font=('Inter', 10, 'bold'))
        log_label.pack(fill='x', padx=10, pady=(5, 0))
        
        self.log_area = scrolledtext.ScrolledText(bottom_frame, wrap=tk.WORD, height=10, font=('Courier New', 9))
        self.log_area.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        self.log_message(0, "[System] โปรแกรม API Tester พร้อมทำงาน...")
        self.log_message(0, f"[System] โหลด {len(self.initial_urls)} URLs สำเร็จ.")

    def _create_request_tab(self, tab_name, url="", method="GET", params_str="", headers_str="", body_json_str="", repeat=""):
        """Creates a new request tab with input fields."""
        self.tab_counter += 1
        order_id = self.tab_counter
        
        # Load defaults from config if not provided
        if not url or url == self.config['DEFAULT_REQUEST']['DEFAULT_URL']: # Only load defaults if initial URL is missing or is the standard fallback
            if not url:
                url = self.config['DEFAULT_REQUEST']['DEFAULT_URL']
            method = self.config['DEFAULT_REQUEST']['DEFAULT_METHOD']
            params_str = self.config['DEFAULT_REQUEST']['DEFAULT_PARAMS']
            headers_str = self.config['DEFAULT_REQUEST']['DEFAULT_HEADERS']
            body_json_str = self.config['DEFAULT_REQUEST']['DEFAULT_PAYLOAD_JSON']
            repeat = self.config['EXECUTION']['DEFAULT_REPEAT_COUNT']
        
        # Main Tab Frame
        tab_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(tab_frame, text=f"ลำดับ {order_id}")
        self.notebook.select(tab_frame)
        
        # --- Request Details Frame ---
        req_frame = ttk.Frame(tab_frame)
        req_frame.pack(fill='x', pady=5)
        
        # URL and Method Input
        method_options = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD']
        method_var = tk.StringVar(value=method)
        
        ttk.Label(req_frame, text="Method:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        ttk.Combobox(req_frame, textvariable=method_var, values=method_options, width=7).grid(row=0, column=1, padx=5, pady=5, sticky='w')

        ttk.Label(req_frame, text="URL:").grid(row=0, column=2, padx=5, pady=5, sticky='w')
        url_entry = ttk.Entry(req_frame, width=50) # นี่คือช่องกรอกลิงก์
        url_entry.insert(0, url)
        url_entry.grid(row=0, column=3, padx=5, pady=5, sticky='ew')
        
        # Execution Settings
        ttk.Label(req_frame, text="Repeat:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        repeat_entry = ttk.Entry(req_frame, width=5)
        repeat_entry.insert(0, repeat)
        repeat_entry.grid(row=1, column=1, padx=5, pady=5, sticky='w')
        
        ttk.Label(req_frame, text="Delay (s):").grid(row=1, column=2, padx=5, pady=5, sticky='w')
        delay_entry = ttk.Entry(req_frame, width=5)
        delay_entry.insert(0, self.config['EXECUTION']['REPEAT_DELAY_SECONDS'])
        delay_entry.grid(row=1, column=3, padx=5, pady=5, sticky='w')
        
        # Send Button
        send_btn = ttk.Button(req_frame, text="▶️ Send", command=lambda: self._send_current_request(order_id))
        send_btn.grid(row=0, column=4, padx=10, sticky='ns')
        
        # New Button: Open in Browser
        open_browser_btn = ttk.Button(req_frame, text="🌐 เปิดในเบราว์เซอร์", command=lambda: self._open_in_browser(order_id))
        open_browser_btn.grid(row=1, column=4, padx=10, sticky='ns') 

        req_frame.grid_columnconfigure(3, weight=1) # Make URL entry expand

        # --- Request Data Notebook (Params, Headers, Body) ---
        data_notebook = ttk.Notebook(tab_frame)
        data_notebook.pack(fill='x', pady=10)

        # Tab 1: Parameters
        params_tab = ttk.Frame(data_notebook, padding="5")
        params_text_area = scrolledtext.ScrolledText(params_tab, wrap=tk.WORD, height=5)
        params_text_area.insert(tk.END, params_str)
        params_text_area.pack(fill='both', expand=True)
        data_notebook.add(params_tab, text="Parameters (Key: Value)")

        # Tab 2: Headers
        headers_tab = ttk.Frame(data_notebook, padding="5")
        headers_text_area = scrolledtext.ScrolledText(headers_tab, wrap=tk.WORD, height=5)
        headers_text_area.insert(tk.END, headers_str)
        headers_text_area.pack(fill='both', expand=True)
        data_notebook.add(headers_tab, text="Headers (Key: Value)")
        
        # Tab 3: Body (JSON/Text)
        body_tab = ttk.Frame(data_notebook, padding="5")
        body_text_area = scrolledtext.ScrolledText(body_tab, wrap=tk.WORD, height=5)
        body_text_area.insert(tk.END, body_json_str)
        body_text_area.pack(fill='both', expand=True)
        data_notebook.add(body_tab, text="Body (JSON/Text)")

        # --- Response Body ---
        ttk.Label(tab_frame, text="Response Body:", font=('Inter', 10, 'bold')).pack(fill='x', pady=(5, 0))
        response_body_text_area = scrolledtext.ScrolledText(tab_frame, wrap=tk.WORD, height=15, font=('Courier New', 9))
        response_body_text_area.pack(fill='both', expand=True)
        
        # Store input widgets and response body widget in the state dictionary
        self.request_data[order_id] = {
            'method': method_var,
            'url': url_entry,
            'repeat': repeat_entry,
            'delay': delay_entry,
            'params': params_text_area,
            'headers': headers_text_area,
            'body': body_text_area,
            'tab_frame': tab_frame,
            'send_button': send_btn 
        }
        self.tab_response_body[order_id] = response_body_text_area

    def _delete_current_tab(self):
        """Deletes the currently selected tab."""
        if self.notebook.select():
            current_tab_id = self.notebook.index(self.notebook.select()) + 1
            current_tab = self.notebook.select()
            
            # Remove from internal data structures
            keys_to_delete = [k for k, v in self.request_data.items() if v['tab_frame'] == current_tab]
            if keys_to_delete:
                del self.request_data[keys_to_delete[0]]
                del self.tab_response_body[keys_to_delete[0]]

            # Remove from Notebook widget
            self.notebook.forget(current_tab)
            self.log_message(0, f"[System] ลบลำดับที่ {current_tab_id} สำเร็จ.")

    def _open_in_browser(self, order_id):
        """Opens the current tab's URL in the user's default web browser."""
        data = self.request_data.get(order_id)
        if data:
            url = data['url'].get()
            if url:
                self.log_message(order_id, f"[System] กำลังเปิดลิงก์ในเบราว์เซอร์: {url[:50]}...")
                webbrowser.open(url)
            else:
                messagebox.showwarning("Warning", "กรุณาใส่ URL ก่อนเปิดในเบราว์เซอร์")

    def _send_current_request(self, order_id):
        """Starts the request sending process in a separate thread."""
        if self.is_sending:
            messagebox.showinfo("Wait", "โปรแกรมกำลังทำงานอยู่ กรุณารอให้เสร็จสิ้นก่อน")
            return

        data = self.request_data.get(order_id)
        if not data: return

        # Validate Repeat and Delay
        try:
            repeat_count = int(data['repeat'].get())
            delay_sec = float(data['delay'].get())
        except ValueError:
            messagebox.showerror("Error", "Repeat และ Delay ต้องเป็นตัวเลขที่ถูกต้อง")
            return
            
        if not data['url'].get():
            messagebox.showwarning("Warning", "กรุณาใส่ URL เป้าหมาย")
            return

        # Disable UI during sending
        data['send_button'].config(state=tk.DISABLED)
        self.is_sending = True
        self.status_var.set("กำลังส่ง Request...")

        # Start the thread
        threading.Thread(target=self._send_request_thread, args=(order_id, data, repeat_count, delay_sec), daemon=True).start()

    def _send_request_thread(self, order_id, data, repeat_count, delay_sec):
        """Handles sending requests repeatedly in a non-blocking thread."""
        
        self.log_message(order_id, f"--- เริ่มการทำงานของลำดับที่ {order_id} ---")
        self.log_message(order_id, f"--- Request Initiated ({repeat_count} Repeats) ---")
        
        # Get selected coins (for log or future API usage)
        selected_coins = [coin for coin, var in self.coin_vars.items() if var.get()]
        coin_info = f"Selected Coins: {selected_coins}" if selected_coins else "No Coins Selected."
        self.log_message(order_id, coin_info)

        results = []
        try:
            for i in range(1, repeat_count + 1):
                self.log_message(order_id, f"Run {i}/{repeat_count} > Starting {data['method'].get()} Request...")
                self.status_var.set(f"กำลังทำงาน: ลำดับ {order_id} ({i}/{repeat_count})")
                
                # Call HTTP Sender
                response = self.sender.send(
                    method=data['method'].get(),
                    url=data['url'].get(),
                    params_str=data['params'].get("1.0", tk.END),
                    headers_str=data['headers'].get("1.0", tk.END),
                    body_json_str=data['body'].get("1.0", tk.END)
                )
                
                results.append(response)

                # Update Log and Response Body
                self.log_message(order_id, f"Run {i}/{repeat_count} > สถานะ: {response['status_code']} {response['status_text']}, เวลา: {response['elapsed_time']}ms, ขนาด: {response['size']} bytes")
                
                # Display response body only from the last successful run
                if response['body']:
                    self.tab_response_body[order_id].delete("1.0", tk.END)
                    self.tab_response_body[order_id].insert(tk.END, response['body'])
                
                # Delay for next run
                if i < repeat_count:
                    time.sleep(delay_sec)

            self.log_message(order_id, f"**SUCCESS!** การส่งคำขอ {repeat_count}/{repeat_count} รอบเสร็จสมบูรณ์")

        except Exception as e:
            self.log_message(order_id, f"*** ERROR: {e} ***")
            self.status_var.set("เกิดข้อผิดพลาด")

        finally:
            # Re-enable UI
            self.master.after(0, self._finalize_send, order_id, data['send_button'])

    def _finalize_send(self, order_id, send_button):
        """Updates status and re-enables UI elements."""
        send_button.config(state=tk.NORMAL)
        self.is_sending = False
        
        # --- Simulated Balance/Result Update ---
        # This is where you would normally parse the API response to get the real balance/result
        # For demonstration, we simulate an update:
        
        # Simulate result/balance change
        new_balance = round(random.uniform(100.00, 2000.00), 2)
        new_bet = random.choice([10, 20, 30, 50])
        
        # Simulate win/loss
        if new_balance > float(self.balance_var.get().split()[0] or 0):
            result = f"+{round(new_balance - float(self.balance_var.get().split()[0] or 0), 2)} 🟢"
        else:
            result = f"-{round(float(self.balance_var.get().split()[0] or 0) - new_balance, 2)} 🔴"

        self.balance_var.set(f"{new_balance:.2f} บาท")
        self.bet_var.set(str(new_bet))
        self.result_var.set(result)
        self.status_var.set("พร้อมทำงาน...")
        
    def log_message(self, order_id, message):
        """Appends a timestamped message to the log area."""
        timestamp = time.strftime("[%H:%M:%S]")
        prefix = f"[ลำดับ {order_id}] " if order_id > 0 else ""
        full_message = f"{timestamp} {prefix}{message}\n"
        
        self.log_area.insert(tk.END, full_message)
        self.log_area.see(tk.END) # Auto-scroll to the bottom

if __name__ == '__main__':
    root = tk.Tk()
    style = ttk.Style()
    style.theme_use('clam') # Use 'clam' theme for better aesthetics
    app = App(root)
    root.mainloop() encoding='utf-8') as f:
                    urls = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
                
                if urls:
                    self.log_message(0, f"[System] โหลด {len(urls)} URLs จากไฟล์ '{file_path}' สำเร็จ. สร้างแท็บใหม่...")
                    
                    # Close all existing tabs before creating new ones
                    for tab_id in self.notebook.tabs():
                        self.notebook.forget(tab_id)
                    self.request_data = {}
                    self.tab_response_body = {}
                    self.tab_counter = 0

                    for i, url in enumerate(urls, 1):
                        self._create_request_tab(f"ลำดับ {i}", url=url)
                else:
                    self.log_message(0, f"[System] ไฟล์ '{file_path}' ว่างเปล่าหรือไม่มีลิงก์.", is_error=True)
            
            except Exception as e:
                self.log_message(0, f"[System] Error ในการโหลดไฟล์: {e}", is_error=True)


    def _send_current_request(self, order_id):
        """Collects data from the current tab and starts the sending thread."""
        data = self.request_data.get(order_id)
        if not data:
            self.log_message(0, f"[System] Error: ไม่พบข้อมูลสำหรับลำดับที่ {order_id}", is_error=True)
            return

        try:
            # 1. Collect Data from Widgets
            url = data['url'].get()
            method = data['method'].get()
            repeat_count = int(data['repeat'].get())
            delay = float(data['delay'].get())
            params_str = data['params'].get('1.0', tk.END).strip()
            headers_str = data['headers'].get('1.0', tk.END).strip()
            body_json_str = data['body'].get('1.0', tk.END).strip()

            # 2. Convert string inputs to dict
            params = self._parse_key_value_string(params_str)
            headers = self._parse_key_value_string(headers_str)
            
            # 3. Disable button and start thread
            data['send_button']['state'] = tk.DISABLED
            self.log_message(order_id, f"--- เริ่มการทำงานของลำดับที่ {order_id} ---")
            
            # Clear previous response body
            self.tab_response_body[order_id].config(state='normal')
            self.tab_response_body[order_id].delete('1.0', tk.END)
            self.tab_response_body[order_id].config(state='disabled')


            thread = threading.Thread(
                target=self.send_request_thread,
                args=(order_id, url, method, params, headers, body_json_str, repeat_count, delay)
            )
            thread.daemon = True
            thread.start()

        except ValueError:
            messagebox.showerror("Error", "Repeat Count และ Delay ต้องเป็นตัวเลขที่ถูกต้อง!")
            data['send_button']['state'] = tk.NORMAL
        except Exception as e:
            messagebox.showerror("Error", f"เกิดข้อผิดพลาดในการเตรียม Request: {e}")
            data['send_button']['state'] = tk.NORMAL

    def _parse_key_value_string(self, text):
        """Converts key: value string (newline or comma separated) to a dictionary."""
        d = {}
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
            try:
                key, value = line.split(':', 1)
                d[key.strip()] = value.strip()
            except ValueError:
                # Handle comma separated values if they don't use new lines
                for part in line.split(','):
                    part = part.strip()
                    if not part: continue
                    try:
                        key, value = part.split(':', 1)
                        d[key.strip()] = value.strip()
                    except ValueError:
                         # Log error if format is wrong, but continue
                        self.log_message(0, f"คำเตือน: ข้อมูล Key/Value '{part}' ไม่ถูกต้อง", is_error=True)
        return d

    def send_request_thread(self, order_id, url, method, params, headers, body, repeat_count, delay):
        """Worker thread for sending the request using HTTPSender."""
        
        # Simulate initial bet amount for demonstration
        current_bet = random.randint(10, 50)
        self.bet_amount_var.set(str(current_bet))
        
        # Simulate initial balance for demonstration
        current_balance = float(self.balance_var.get().replace(' บาท', ''))
        
        # Run the HTTP request logic
        self.http_sender.send_request(order_id, url, method, params, headers, body, repeat_count, delay)
        
        # After completion, update general status (Simulated)
        if self.http_sender.running:
            # Simulate win/loss and update balance
            profit = round(random.uniform(-100, 150), 2)
            
            if profit >= 0:
                self.win_loss_var.set(f"+{profit:.2f} 🟢")
            else:
                self.win_loss_var.set(f"{profit:.2f} 🔴")
                
            new_balance = current_balance + profit
            self.balance_var.set(f"{new_balance:.2f} บาท")
        else:
            self.win_loss_var.set("หยุดทำงาน")

        # Re-enable the Send button
        self.request_data[order_id]['send_button']['state'] = tk.NORMAL

    def log_message(self, order_id, message, is_error=False, is_response_body=False):
        """Inserts a message into the main log area or the tab's response body."""
        if is_response_body:
            # Update the specific Response Body of the tab
            response_widget = self.tab_response_body.get(order_id)
            if response_widget:
                response_widget.config(state='normal')
                response_widget.insert('1.0', message)
                response_widget.config(state='disabled')
        else:
            # Update the main Log Area
            self.log_area.config(state='normal')
            
            prefix = ""
            if order_id > 0:
                prefix = f"[ลำดับ {order_id}] "
                
            tag = "error" if is_error else "normal"
            
            self.log_area.insert(tk.END, f"{prefix}{message}\n", tag)
            self.log_area.tag_config("error", foreground="red")
            self.log_area.tag_config("normal", foreground="black")
            
            self.log_area.yview(tk.END)
            self.log_area.config(state='disabled')

if __name__ == '__main__':
    root = tk.Tk()
    app = App(root)
    root.mainloop() encoding='utf-8') as f:
                    urls = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
                
                if urls:
                    self.log_message(0, f"[System] โหลด {len(urls)} URLs จากไฟล์ '{file_path}' สำเร็จ. สร้างแท็บใหม่...")
                    
                    # Close all existing tabs before creating new ones
                    for tab_id in self.notebook.tabs():
                        self.notebook.forget(tab_id)
                    self.request_data = {}
                    self.tab_response_body = {}
                    self.tab_counter = 0

                    for i, url in enumerate(urls, 1):
                        self._create_request_tab(f"ลำดับ {i}", url=url)
                else:
                    self.log_message(0, f"[System] ไฟล์ '{file_path}' ว่างเปล่าหรือไม่มีลิงก์.", is_error=True)
            
            except Exception as e:
                self.log_message(0, f"[System] Error ในการโหลดไฟล์: {e}", is_error=True)


    def _send_current_request(self, order_id):
        """Collects data from the current tab and starts the sending thread."""
        data = self.request_data.get(order_id)
        if not data:
            self.log_message(0, f"[System] Error: ไม่พบข้อมูลสำหรับลำดับที่ {order_id}", is_error=True)
            return

        try:
            # 1. Collect Data from Widgets
            url = data['url'].get()
            method = data['method'].get()
            repeat_count = int(data['repeat'].get())
            delay = float(data['delay'].get())
            params_str = data['params'].get('1.0', tk.END).strip()
            headers_str = data['headers'].get('1.0', tk.END).strip()
            body_json_str = data['body'].get('1.0', tk.END).strip()

            # 2. Convert string inputs to dict
            params = self._parse_key_value_string(params_str)
            headers = self._parse_key_value_string(headers_str)
            
            # 3. Disable button and start thread
            data['send_button']['state'] = tk.DISABLED
            self.log_message(order_id, f"--- เริ่มการทำงานของลำดับที่ {order_id} ---")
            
            # Clear previous response body
            self.tab_response_body[order_id].config(state='normal')
            self.tab_response_body[order_id].delete('1.0', tk.END)
            self.tab_response_body[order_id].config(state='disabled')


            thread = threading.Thread(
                target=self.send_request_thread,
                args=(order_id, url, method, params, headers, body_json_str, repeat_count, delay)
            )
            thread.daemon = True
            thread.start()

        except ValueError:
            messagebox.showerror("Error", "Repeat Count และ Delay ต้องเป็นตัวเลขที่ถูกต้อง!")
            data['send_button']['state'] = tk.NORMAL
        except Exception as e:
            messagebox.showerror("Error", f"เกิดข้อผิดพลาดในการเตรียม Request: {e}")
            data['send_button']['state'] = tk.NORMAL

    def _parse_key_value_string(self, text):
        """Converts key: value string (newline or comma separated) to a dictionary."""
        d = {}
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
            try:
                key, value = line.split(':', 1)
                d[key.strip()] = value.strip()
            except ValueError:
                # Handle comma separated values if they don't use new lines
                for part in line.split(','):
                    part = part.strip()
                    if not part: continue
                    try:
                        key, value = part.split(':', 1)
                        d[key.strip()] = value.strip()
                    except ValueError:
                         # Log error if format is wrong, but continue
                        self.log_message(0, f"คำเตือน: ข้อมูล Key/Value '{part}' ไม่ถูกต้อง", is_error=True)
        return d

    def send_request_thread(self, order_id, url, method, params, headers, body, repeat_count, delay):
        """Worker thread for sending the request using HTTPSender."""
        
        # Simulate initial bet amount for demonstration
        current_bet = random.randint(10, 50)
        self.bet_amount_var.set(str(current_bet))
        
        # Simulate initial balance for demonstration
        current_balance = float(self.balance_var.get().replace(' บาท', ''))
        
        # Run the HTTP request logic
        self.http_sender.send_request(order_id, url, method, params, headers, body, repeat_count, delay)
        
        # After completion, update general status (Simulated)
        if self.http_sender.running:
            # Simulate win/loss and update balance
            profit = round(random.uniform(-100, 150), 2)
            
            if profit >= 0:
                self.win_loss_var.set(f"+{profit:.2f} 🟢")
            else:
                self.win_loss_var.set(f"{profit:.2f} 🔴")
                
            new_balance = current_balance + profit
            self.balance_var.set(f"{new_balance:.2f} บาท")
        else:
            self.win_loss_var.set("หยุดทำงาน")

        # Re-enable the Send button
        self.request_data[order_id]['send_button']['state'] = tk.NORMAL

    def log_message(self, order_id, message, is_error=False, is_response_body=False):
        """Inserts a message into the main log area or the tab's response body."""
        if is_response_body:
            # Update the specific Response Body of the tab
            response_widget = self.tab_response_body.get(order_id)
            if response_widget:
                response_widget.config(state='normal')
                response_widget.insert('1.0', message)
                response_widget.config(state='disabled')
        else:
            # Update the main Log Area
            self.log_area.config(state='normal')
            
            prefix = ""
            if order_id > 0:
                prefix = f"[ลำดับ {order_id}] "
                
            tag = "error" if is_error else "normal"
            
            self.log_area.insert(tk.END, f"{prefix}{message}\n", tag)
            self.log_area.tag_config("error", foreground="red")
            self.log_area.tag_config("normal", foreground="black")
            
            self.log_area.yview(tk.END)
            self.log_area.config(state='disabled')

if __name__ == '__main__':
    root = tk.Tk()
    app = App(root)
    root.mainloop()adding="5")
        request_notebook.add(body_frame, text='Body (JSON)')
        body_text_area = tk.Text(body_frame, height=8, font=('Consolas', 10))
        body_text_area.insert('1.0', default_body_json)
        body_text_area.pack(fill='both', expand=True)
        tab_data['body_text_widget'] = body_text_area # เก็บ reference ของ Text Widget

        # 3. Repeat/Delay Bar
        repeat_frame = ttk.Frame(tab_frame, padding="5")
        repeat_frame.pack(fill='x', pady=(5, 0))
        
        ttk.Label(repeat_frame, text="ทำซ้ำ (ครั้ง):").pack(side=tk.LEFT, padx=(0, 5))
        repeat_entry = ttk.Entry(repeat_frame, textvariable=tab_data['repeat_var'], width=5)
        repeat_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(repeat_frame, text="หน่วงเวลา (วิ):").pack(side=tk.LEFT, padx=(0, 5))
        delay_entry = ttk.Entry(repeat_frame, textvariable=tab_data['delay_var'], width=5)
        delay_entry.pack(side=tk.LEFT)
        
        # สถานะเฉพาะแท็บ
        tab_status_label = ttk.Label(repeat_frame, textvariable=tab_data['status_var'], foreground='blue')
        tab_status_label.pack(side=tk.RIGHT, padx=(10, 0))


    def close_tab(self, level_to_close):
        """Closes the specified tab based on its level."""
        for i, tab in enumerate(self.notebook.tabs()):
            if self.notebook.tab(tab, "text") == f"ลำดับ {level_to_close}":
                self.notebook.forget(tab)
                # ลบข้อมูลออกจาก dictionary
                if level_to_close in self.request_tabs_data:
                    del self.request_tabs_data[level_to_close]
                self.log_message(f"[System] ปิดแท็บ: ลำดับ {level_to_close}")
                return

    def log_message(self, message):
        """Appends a message to the main response log area."""
        self.log_text_area.insert(tk.END, f"{message}\n")
        self.log_text_area.see(tk.END) # Scroll to the bottom

    def update_bet_status(self, message):
        """Updates the general status bar (ยอดเดิมพัน/ผลได้เสีย)."""
        self.bet_status_var.set(message)

    def update_tab_status(self, level, message):
        """Updates the status bar for a specific tab."""
        if level in self.request_tabs_data:
            self.request_tabs_data[level]['status_var'].set(message)
            
    def get_coin_states(self):
        """Retrieves the current state of all coin checkboxes."""
        states = {}
        for coin, var in self.coin_vars.items():
            states[coin] = var.get()
        return states

    def send_request(self, level):
        """Gathers data from UI and starts the request in a new thread."""
        if level not in self.request_tabs_data:
            self.log_message(f"!!! ข้อผิดพลาด: ไม่พบข้อมูลสำหรับลำดับ {level}.")
            return

        tab_data = self.request_tabs_data[level]
        
        # 1. ดึงข้อมูลล่าสุดจาก Text Widgets
        # Note: ใช้ .get('1.0', tk.END).strip() เพื่อดึงค่าจาก Text Widget
        request_data = {
            'level': level,
            'url': tab_data['url_var'].get(),
            'method': tab_data['method_var'].get(),
            'params': tab_data['params_text_widget'].get('1.0', tk.END).strip(),
            'headers': tab_data['headers_text_widget'].get('1.0', tk.END).strip(),
            'body': tab_data['body_text_widget'].get('1.0', tk.END).strip(),
        }
        
        try:
            repeat_count = int(tab_data['repeat_var'].get())
            delay = float(tab_data['delay_var'].get())
        except ValueError:
            self.log_message(f"[ลำดับ {level}] !!! ข้อผิดพลาด: จำนวนครั้งที่ทำซ้ำหรือการหน่วงเวลาต้องเป็นตัวเลขที่ถูกต้อง.")
            return
            
        # 2. ดึงสถานะการเลือกเหรียญ
        coin_states = self.get_coin_states()

        # 3. อัปเดตสถานะเริ่มต้น
        self.update_tab_status(level, "กำลังส่ง...")
        self.log_message(f"\n[ลำดับ {level}] --- เริ่มต้น Request ---")

        # 4. เริ่มส่ง Request ใน Thread ใหม่ (ป้องกัน UI ค้าง)
        thread = threading.Thread(
            target=http_sender.send_request_logic,
            args=(request_data, self.log_message, self.update_bet_status, repeat_count, delay, coin_states)
        )
        thread.daemon = True # ทำให้ Thread ปิดตัวเองเมื่อโปรแกรมหลักปิด
        thread.start()
        
        # 5. อัปเดตสถานะของแท็บเมื่อ Thread เริ่ม
        self.update_tab_status(level, f"กำลังทำงาน ({repeat_count}x)...")
        # ใช้ after() เพื่อตรวจสอบสถานะ Thread และอัปเดตเมื่อเสร็จสิ้น
        self.master.after(100, lambda: self._check_thread_completion(thread, level))

    def _check_thread_completion(self, thread, level):
        """Checks if the request thread has finished and updates the status."""
        if thread.is_alive():
            # ถ้า Thread ยังทำงานอยู่ ให้เช็คซ้ำใน 100ms
            self.master.after(100, lambda: self._check_thread_completion(thread, level))
        else:
            # ถ้า Thread เสร็จแล้ว
            self.update_tab_status(level, "เสร็จสิ้น.")
            self.log_message(f"[ลำดับ {level}] --- Request Thread ทำงานเสร็จสมบูรณ์ ---")


if __name__ == "__main__":
    # ตรวจสอบว่ามีไฟล์ config.ini หรือไม่
    if not os.path.exists('config.ini'):
        print("ERROR: ไม่พบไฟล์ config.ini กรุณาสร้างไฟล์ตาม Template ที่ให้ไว้.")
    else:
        root = tk.Tk()
        app = App(root)
        root.mainloop()