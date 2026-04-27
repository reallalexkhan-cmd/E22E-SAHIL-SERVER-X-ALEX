# Developer: Darkstar Boii Sahiil
# FHIR System - Flask Backend
# Full Power, Full Stack, Deploy Anywhere

from flask import Flask, render_template, request, jsonify, make_response, redirect, url_for
from flask_cors import CORS
import threading
import time
import json
import os
from pathlib import Path
import database as db

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'darkstar-boii-sahiil-fhir-secret-2026')
CORS(app, supports_credentials=True)

PORT = int(os.environ.get('PORT', 20139))

# In-memory automation states per user
automation_states = {}

class AutomationState:
    def __init__(self):
        self.running = False
        self.message_count = 0
        self.logs = []
        self.message_rotation_index = 0
        self.thread = None

    def to_dict(self):
        return {
            'running': self.running,
            'message_count': self.message_count,
            'logs': self.logs[-50:],
        }

def get_automation_state(user_id):
    if user_id not in automation_states:
        automation_states[user_id] = AutomationState()
    return automation_states[user_id]

def log_message(user_id, msg, log_type='info'):
    timestamp = time.strftime("%H:%M:%S")
    formatted = f"[{timestamp}] {msg}"
    state = get_automation_state(user_id)
    state.logs.append({'time': timestamp, 'message': msg, 'type': log_type, 'full': formatted})
    if len(state.logs) > 200:
        state.logs = state.logs[-200:]
    db.add_log(user_id, msg, log_type)

def find_message_input(driver, process_id, user_id):
    log_message(user_id, f'{process_id}: Finding message input...', 'info')
    time.sleep(10)
    try:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)
    except:
        pass

    try:
        page_title = driver.title
        page_url = driver.current_url
        log_message(user_id, f'{process_id}: Page: {page_title} | URL: {page_url}', 'info')
    except Exception as e:
        log_message(user_id, f'{process_id}: Could not get page info: {e}', 'warning')

    selectors = [
        'div[contenteditable="true"][role="textbox"]',
        'div[contenteditable="true"][data-lexical-editor="true"]',
        'div[aria-label*="message" i][contenteditable="true"]',
        'div[aria-label*="Message" i][contenteditable="true"]',
        'div[contenteditable="true"][spellcheck="true"]',
        '[role="textbox"][contenteditable="true"]',
        'textarea[placeholder*="message" i]',
        'div[aria-placeholder*="message" i]',
        'div[data-placeholder*="message" i]',
        '[contenteditable="true"]',
        'textarea',
        'input[type="text"]'
    ]

    from selenium.webdriver.common.by import By
    log_message(user_id, f'{process_id}: Trying {len(selectors)} selectors...', 'info')

    for idx, selector in enumerate(selectors):
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for element in elements:
                try:
                    is_editable = driver.execute_script("""
                        return arguments[0].contentEditable === 'true' ||
                               arguments[0].tagName === 'TEXTAREA' ||
                               arguments[0].tagName === 'INPUT';
                    """, element)
                    if is_editable:
                        try:
                            element.click()
                            time.sleep(0.5)
                        except:
                            pass
                        element_text = driver.execute_script(
                            "return arguments[0].placeholder || arguments[0].getAttribute('aria-label') || arguments[0].getAttribute('aria-placeholder') || '';",
                            element
                        ).lower()
                        keywords = ['message', 'write', 'type', 'send', 'chat', 'msg', 'reply', 'text', 'aa']
                        if any(k in element_text for k in keywords):
                            log_message(user_id, f'{process_id}: ✅ Found message input: {element_text[:50]}', 'success')
                            return element
                        elif idx < 10:
                            log_message(user_id, f'{process_id}: ✅ Using primary selector #{idx+1}', 'success')
                            return element
                        elif selector in ['[contenteditable="true"]', 'textarea', 'input[type="text"]']:
                            log_message(user_id, f'{process_id}: ✅ Using fallback element', 'success')
                            return element
                except Exception as e:
                    continue
        except:
            continue
    return None

def setup_browser(user_id):
    log_message(user_id, 'Setting up Chrome browser...', 'info')
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service

    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-setuid-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36')

    for path in ['/usr/bin/chromium', '/usr/bin/chromium-browser', '/usr/bin/google-chrome', '/usr/bin/chrome']:
        if Path(path).exists():
            chrome_options.binary_location = path
            log_message(user_id, f'Found Chromium at: {path}', 'info')
            break

    driver_path = None
    for p in ['/usr/bin/chromedriver', '/usr/local/bin/chromedriver']:
        if Path(p).exists():
            driver_path = p
            break

    try:
        if driver_path:
            service = Service(executable_path=driver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)
        else:
            driver = webdriver.Chrome(options=chrome_options)
        driver.set_window_size(1920, 1080)
        log_message(user_id, 'Chrome browser setup completed!', 'success')
        return driver
    except Exception as e:
        log_message(user_id, f'Browser setup failed: {e}', 'error')
        raise e

def send_messages_thread(config, user_id, process_id='AUTO-1'):
    state = get_automation_state(user_id)
    driver = None
    try:
        log_message(user_id, f'{process_id}: Starting automation...', 'info')
        driver = setup_browser(user_id)

        log_message(user_id, f'{process_id}: Navigating to Facebook...', 'info')
        driver.get('https://www.facebook.com/')
        time.sleep(8)

        if config.get('cookies', '').strip():
            log_message(user_id, f'{process_id}: Adding cookies...', 'info')
            for cookie in config['cookies'].split(';'):
                cookie_trimmed = cookie.strip()
                if cookie_trimmed:
                    eq_idx = cookie_trimmed.find('=')
                    if eq_idx > 0:
                        name = cookie_trimmed[:eq_idx].strip()
                        value = cookie_trimmed[eq_idx+1:].strip()
                        try:
                            driver.add_cookie({'name': name, 'value': value, 'domain': '.facebook.com', 'path': '/'})
                        except:
                            pass

        if config.get('chat_id'):
            chat_id = config['chat_id'].strip()
            log_message(user_id, f'{process_id}: Opening conversation {chat_id}...', 'info')
            driver.get(f'https://www.facebook.com/messages/e2ee/t/{chat_id}')
            time.sleep(5)
            if '/messages/e2ee' not in driver.current_url and '/e2ee/t/' not in driver.current_url:
                driver.get(f'https://www.facebook.com/messages/t/{chat_id}')
        else:
            driver.get('https://www.facebook.com/messages')

        time.sleep(15)
        message_input = find_message_input(driver, process_id, user_id)

        if not message_input:
            log_message(user_id, f'{process_id}: Message input not found!', 'error')
            state.running = False
            db.set_automation_running(user_id, False)
            return 0

        delay = int(config.get('delay', 30))
        messages_list = [m.strip() for m in config.get('messages', '').split('\n') if m.strip()]
        if not messages_list:
            messages_list = ['Hello!']

        messages_sent = 0
        rot_idx = 0

        while state.running:
            base_message = messages_list[rot_idx % len(messages_list)]
            rot_idx += 1
            if config.get('name_prefix'):
                message_to_send = f"{config['name_prefix']} {base_message}"
            else:
                message_to_send = base_message

            try:
                driver.execute_script("""
                    const element = arguments[0];
                    const message = arguments[1];
                    element.scrollIntoView({behavior: 'smooth', block: 'center'});
                    element.focus();
                    element.click();
                    if (element.tagName === 'DIV') {
                        element.textContent = message;
                        element.innerHTML = message;
                    } else {
                        element.value = message;
                    }
                    element.dispatchEvent(new Event('input', { bubbles: true }));
                    element.dispatchEvent(new Event('change', { bubbles: true }));
                    element.dispatchEvent(new InputEvent('input', { bubbles: true, data: message }));
                """, message_input, message_to_send)

                time.sleep(1)

                sent = driver.execute_script("""
                    const sendButtons = document.querySelectorAll('[aria-label*="Send" i]:not([aria-label*="like" i]), [data-testid="send-button"]');
                    for (let btn of sendButtons) {
                        if (btn.offsetParent !== null) { btn.click(); return 'button_clicked'; }
                    }
                    return 'button_not_found';
                """)

                if sent == 'button_not_found':
                    driver.execute_script("""
                        const element = arguments[0];
                        element.focus();
                        const events = [
                            new KeyboardEvent('keydown', {key:'Enter',code:'Enter',keyCode:13,which:13,bubbles:true}),
                            new KeyboardEvent('keypress',{key:'Enter',code:'Enter',keyCode:13,which:13,bubbles:true}),
                            new KeyboardEvent('keyup',  {key:'Enter',code:'Enter',keyCode:13,which:13,bubbles:true})
                        ];
                        events.forEach(e => element.dispatchEvent(e));
                    """, message_input)
                    log_message(user_id, f'{process_id}: ✅ Sent via Enter: "{message_to_send[:30]}..."', 'success')
                else:
                    log_message(user_id, f'{process_id}: ✅ Sent via button: "{message_to_send[:30]}..."', 'success')

                messages_sent += 1
                state.message_count = messages_sent
                log_message(user_id, f'{process_id}: Message #{messages_sent} sent. Waiting {delay}s...', 'info')
                time.sleep(delay)

            except Exception as e:
                log_message(user_id, f'{process_id}: Send error: {str(e)[:100]}', 'error')
                time.sleep(5)

        log_message(user_id, f'{process_id}: Automation stopped. Total: {messages_sent}', 'info')
        return messages_sent

    except Exception as e:
        log_message(user_id, f'{process_id}: Fatal error: {str(e)}', 'error')
        state.running = False
        db.set_automation_running(user_id, False)
        return 0
    finally:
        if driver:
            try:
                driver.quit()
                log_message(user_id, f'{process_id}: Browser closed', 'info')
            except:
                pass

# ─────────────────────── AUTH HELPERS ───────────────────────
def get_current_user():
    token = request.cookies.get('session_token')
    if not token:
        return None
    user_id = db.verify_session(token)
    if not user_id:
        return None
    username = db.get_username(user_id)
    return {'id': user_id, 'username': username}

def require_auth(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            if request.is_json:
                return jsonify({'success': False, 'error': 'Not authenticated'}), 401
            return redirect('/')
        return f(*args, user=user, **kwargs)
    return decorated

# ─────────────────────── ROUTES ───────────────────────

@app.route('/')
def index():
    user = get_current_user()
    if user:
        return redirect('/dashboard')
    return render_template('index.html')

@app.route('/dashboard')
@require_auth
def dashboard(user):
    return render_template('dashboard.html', username=user['username'], user_id=user['id'])

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    if not username or not password:
        return jsonify({'success': False, 'error': 'Username and password required'})
    user_id = db.verify_user(username, password)
    if not user_id:
        return jsonify({'success': False, 'error': 'Invalid username or password'})
    token = db.create_session(user_id)
    resp = make_response(jsonify({'success': True, 'username': username, 'user_id': user_id}))
    resp.set_cookie('session_token', token, max_age=7*24*3600, httponly=True, samesite='Lax')
    return resp

@app.route('/api/auth/register', methods=['POST'])
def api_register():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    confirm = data.get('confirm_password', '').strip()
    if not username or not password:
        return jsonify({'success': False, 'error': 'All fields are required'})
    if password != confirm:
        return jsonify({'success': False, 'error': 'Passwords do not match'})
    if len(password) < 6:
        return jsonify({'success': False, 'error': 'Password must be at least 6 characters'})
    success, message = db.create_user(username, password)
    return jsonify({'success': success, 'message': message if success else None, 'error': message if not success else None})

@app.route('/api/auth/logout', methods=['POST'])
def api_logout():
    token = request.cookies.get('session_token')
    if token:
        db.delete_session(token)
    resp = make_response(jsonify({'success': True}))
    resp.delete_cookie('session_token')
    return resp

@app.route('/api/config/get', methods=['GET'])
@require_auth
def api_get_config(user):
    config = db.get_user_config(user['id'])
    if config:
        config.pop('cookies', None)
        return jsonify({'success': True, 'config': config})
    return jsonify({'success': False, 'error': 'Config not found'})

@app.route('/api/config/save', methods=['POST'])
@require_auth
def api_save_config(user):
    data = request.get_json()
    config = db.get_user_config(user['id'])
    cookies = data.get('cookies', '').strip()
    if not cookies:
        cookies = config.get('cookies', '') if config else ''
    db.update_user_config(
        user['id'],
        data.get('chat_id', ''),
        data.get('name_prefix', ''),
        int(data.get('delay', 30)),
        cookies,
        data.get('messages', '')
    )
    return jsonify({'success': True, 'message': 'Configuration saved successfully!'})

@app.route('/api/automation/start', methods=['POST'])
@require_auth
def api_start_automation(user):
    user_id = user['id']
    state = get_automation_state(user_id)
    if state.running:
        return jsonify({'success': False, 'error': 'Automation already running'})
    config = db.get_user_config(user_id)
    if not config or not config.get('chat_id'):
        return jsonify({'success': False, 'error': 'Please set Chat ID in configuration first!'})
    state.running = True
    state.message_count = 0
    state.logs = []
    state.message_rotation_index = 0
    db.set_automation_running(user_id, True)
    db.clear_logs(user_id)
    thread = threading.Thread(target=send_messages_thread, args=(config, user_id))
    thread.daemon = True
    thread.start()
    state.thread = thread
    return jsonify({'success': True, 'message': 'Automation started!'})

@app.route('/api/automation/stop', methods=['POST'])
@require_auth
def api_stop_automation(user):
    user_id = user['id']
    state = get_automation_state(user_id)
    state.running = False
    db.set_automation_running(user_id, False)
    return jsonify({'success': True, 'message': 'Automation stopped!'})

@app.route('/api/automation/status', methods=['GET'])
@require_auth
def api_automation_status(user):
    user_id = user['id']
    state = get_automation_state(user_id)
    config = db.get_user_config(user_id)
    chat_id = config.get('chat_id', '') if config else ''
    display_chat = (chat_id[:8] + '...') if chat_id and len(chat_id) > 8 else chat_id
    return jsonify({
        'success': True,
        'running': state.running,
        'message_count': state.message_count,
        'chat_id': display_chat,
        'logs': state.logs[-30:]
    })

@app.route('/api/automation/logs', methods=['GET'])
@require_auth
def api_automation_logs(user):
    logs = db.get_logs(user['id'], 100)
    state = get_automation_state(user['id'])
    return jsonify({'success': True, 'logs': state.logs[-50:], 'db_logs': logs})

@app.route('/api/automation/clear_logs', methods=['POST'])
@require_auth
def api_clear_logs(user):
    db.clear_logs(user['id'])
    state = get_automation_state(user['id'])
    state.logs = []
    return jsonify({'success': True})

@app.route('/api/user/info', methods=['GET'])
@require_auth
def api_user_info(user):
    return jsonify({'success': True, 'username': user['username'], 'user_id': user['id']})

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'service': 'FHIR System', 'developer': 'Darkstar Boii Sahiil'})

if __name__ == '__main__':
    print(f"🚀 FHIR System starting on port {PORT}")
    print(f"   Developer: Darkstar Boii Sahiil")
    print(f"   URL: http://0.0.0.0:{PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False)