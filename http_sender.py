import requests
import json
import time

def safe_eval(data_str):
    """Safely converts string data (like headers or params) into a dictionary."""
    if not data_str:
        return {}
    
    # พยายามแยกเป็น dictionary จาก key: value
    data_dict = {}
    try:
        # แยกแต่ละคู่ key: value โดยใช้ comma
        items = data_str.strip().split(',')
        for item in items:
            if ':' in item:
                key, value = item.split(':', 1)
                data_dict[key.strip()] = value.strip()
    except Exception as e:
        print(f"Error parsing data string '{data_str}': {e}")
        return {}
    return data_dict

def send_request_logic(request_data, log_callback, status_callback, repeat_count, delay, coin_states=None):
    """
    Handles the logic for sending a single or repeated HTTP request.
    
    Args:
        request_data (dict): Dictionary containing URL, method, params, headers, and body.
        log_callback (function): Function to update the main log display.
        status_callback (function): Function to update the status bar (e.g., win/loss).
        repeat_count (int): How many times to repeat the request.
        delay (float): Delay between repeated requests.
        coin_states (dict): States of the coin selection checkboxes (e.g., {'coin_2': True, ...}).
    """
    url = request_data.get('url', 'http://localhost')
    method = request_data.get('method', 'GET').upper()
    params = safe_eval(request_data.get('params', ''))
    headers = safe_eval(request_data.get('headers', ''))
    body_str = request_data.get('body', '')
    
    # --- Check Coin States (For specialized function logging) ---
    if coin_states:
        # แก้ไข cion เป็น coin เพื่อความชัดเจนในโค้ด
        active_coins = [k.replace('coin_', 'เหรียญ ') for k, v in coin_states.items() if v] 
        log_callback(f"[System] เหรียญที่เปิดใช้งานสำหรับเซสชันนี้: {', '.join(active_coins) if active_coins else 'ไม่มี'}")
    
    is_json = False
    json_data = None
    
    if body_str and method in ['POST', 'PUT', 'PATCH']:
        try:
            # พยายามแปลง Body เป็น JSON
            json_data = json.loads(body_str)
            is_json = True
            # ตรวจสอบและตั้งค่า Content-Type
            if 'Content-Type' not in headers and 'content-type' not in headers:
                 headers['Content-Type'] = 'application/json'
        except json.JSONDecodeError:
            log_callback(f"[ลำดับ {request_data.get('level', 0)}] WARNING: Body ไม่ใช่ JSON ที่ถูกต้อง. กำลังส่งเป็น Raw Data.")
            pass # ส่งเป็น data แทน json

    log_callback(f"[ลำดับ {request_data.get('level', 0)}] เริ่มต้น {method} Request ไปยัง: {url}...")
    
    for i in range(repeat_count):
        start_time = time.time()
        log_prefix = f"[ลำดับ {request_data.get('level', 0)}] Run {i + 1}/{repeat_count}"
        
        try:
            response = requests.request(
                method, 
                url, 
                params=params, 
                headers=headers, 
                json=json_data if is_json else None,
                data=body_str if not is_json and body_str else None,
                timeout=10 # ตั้งค่า Timeout
            )
            
            elapsed_time = (time.time() - start_time) * 1000 # เป็นมิลลิวินาที
            
            # --- Response Details ---
            status_code = response.status_code
            response_size = len(response.content)
            
            # --- Log ผลลัพธ์ ---
            log_callback(f"{log_prefix} > สถานะ: {status_code}, เวลา: {elapsed_time:.2f}ms, ขนาด: {response_size} bytes")
            
            # --- จำลองการอัปเดตสถานะ (ผลได้เสีย) ---
            if status_code < 400:
                # จำลองการชนะ/ได้เงิน (Win/Loss Simulation)
                status_callback(f"ยอดเดิมพัน: 100, ผลได้เสีย: +10 (สำเร็จ)")
            else:
                status_callback(f"ยอดเดิมพัน: 100, ผลได้เสีย: -5 (ข้อผิดพลาด)")

            # --- แสดง Response Body (ย่อ) ---
            try:
                # พยายามแสดงผลเป็น JSON ที่จัดระเบียบ
                response_content = json.dumps(response.json(), indent=2)
            except:
                # หากไม่ใช่ JSON
                response_content = response.text
                
            log_callback(f"{log_prefix} > ตัวอย่าง Body: {response_content[:200]}...")

        except requests.exceptions.RequestException as e:
            log_callback(f"{log_prefix} !!! ข้อผิดพลาด: Request ล้มเหลว: {e}")
            status_callback("ยอดเดิมพัน: N/A, ผลได้เสีย: -99 (ข้อผิดพลาด Request)")
        
        if i < repeat_count - 1:
            # หน่วงเวลาก่อนส่งซ้ำครั้งต่อไป
            time.sleep(delay)
    
    log_callback(f"[ลำดับ {request_data.get('level', 0)}] --- เสร็จสิ้นการ Run ทั้งหมด {repeat_count} ครั้ง ---")          # ลบข้อมูลออกจาก dictionary
                if level_to_close in self.request_tabs_data:
                    del self.request_tabs_data[level_to_close]
                self.log_message(f"[System] Closed tab: ลำดับ {level_to_close}")
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
            
    def send_request(self, level):
        """Gathers data from UI and starts the request in a new thread."""
        if level not in self.request_tabs_data:
            self.log_message(f"!!! ERROR: Data for level {level} not found.")
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
            self.log_message(f"[ลำดับ {level}] !!! ERROR: Repeat Count or Delay must be a valid number.")
            return

        # 2. อัปเดตสถานะเริ่มต้น
        self.update_tab_status(level, "Sending...")
        self.log_message(f"\n[ลำดับ {level}] --- Request Initiated ---")

        # 3. เริ่มส่ง Request ใน Thread ใหม่ (ป้องกัน UI ค้าง)
        thread = threading.Thread(
            target=http_sender.send_request_logic,
            args=(request_data, self.log_message, self.update_bet_status, repeat_count, delay)
        )
        thread.daemon = True # ทำให้ Thread ปิดตัวเองเมื่อโปรแกรมหลักปิด
        thread.start()
        
        # 4. อัปเดตสถานะของแท็บเมื่อ Thread เริ่ม
        self.update_tab_status(level, f"Running ({repeat_count}x)...")
        # ใช้ after() เพื่อตรวจสอบสถานะ Thread และอัปเดตเมื่อเสร็จสิ้น
        self.master.after(100, lambda: self._check_thread_completion(thread, level))

    def _check_thread_completion(self, thread, level):
        """Checks if the request thread has finished and updates the status."""
        if thread.is_alive():
            # ถ้า Thread ยังทำงานอยู่ ให้เช็คซ้ำใน 100ms
            self.master.after(100, lambda: self._check_thread_completion(thread, level))
        else:
            # ถ้า Thread เสร็จแล้ว
            self.update_tab_status(level, "Finished.")
            self.log_message(f"[ลำดับ {level}] --- Request Thread Completed ---")


if __name__ == "__main__":
    # ตรวจสอบว่ามีไฟล์ config.ini หรือไม่
    if not os.path.exists('config.ini'):
        print("ERROR: config.ini not found. Please create it using the provided template.")
    else:
        root = tk.Tk()
        app = App(root)
        root.mainloop()