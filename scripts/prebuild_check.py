#!/usr/bin/env python3
"""
Pre-Build Validation for Meditacao Swarm.
Runs at container startup.  Warnings are logged but do NOT block startup.
Only missing REQUIRED env vars (DEEPSEEK_API_KEY, TELEGRAM_BOT_TOKEN) block.
"""
import os, sys, json, time, urllib.request, urllib.error

FATAL = []

def check(name, fn, fatal=False):
    start = time.time()
    try:
        result = fn()
        elapsed = time.time() - start
        status = "PASS" if result else "WARN"
        print(f"  [{status}] {name} ({elapsed:.1f}s)")
        if not result and fatal:
            FATAL.append(name)
        return result
    except Exception as e:
        elapsed = time.time() - start
        label = "FATAL" if fatal else "WARN"
        print(f"  [{label}] {name} ({elapsed:.1f}s) -> {e}")
        if fatal:
            FATAL.append(name)
        return False

print("Meditacao Swarm - Pre-Build Validation")
print(f"{time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
print()

# 0. Required env vars (FATAL if missing)
def check_ds_key():
    return bool(os.environ.get("DEEPSEEK_API_KEY", ""))
def check_tg_key():
    return bool(os.environ.get("TELEGRAM_BOT_TOKEN", ""))
def check_bs_key():
    return bool(os.environ.get("BASEROW_TOKEN", ""))

print("0. Required Env Vars")
check("DEEPSEEK_API_KEY set", check_ds_key, fatal=True)
check("TELEGRAM_BOT_TOKEN set", check_tg_key, fatal=True)
check("BASEROW_TOKEN set", check_bs_key, fatal=True)
print()

# 1. DeepSeek API connectivity (warn only - network may not be ready)
DS_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DS_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-pro")
DS_BASE = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")

def check_deepseek():
    data = json.dumps({
        "model": DS_MODEL,
        "messages": [{"role": "user", "content": "OK"}],
        "max_tokens": 3, "temperature": 0
    }).encode()
    req = urllib.request.Request(f"{DS_BASE}/chat/completions", data=data,
        headers={"Authorization": f"Bearer {DS_KEY}", "Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=15)
    return True

print("1. External APIs (non-fatal)")
check("DeepSeek API reachable", check_deepseek, fatal=False)
print()

# 2. Internal Swarm DNS
def check_dns():
    import socket
    socket.gethostbyname("matos-soares")
    return True
print("2. Internal Network")
check("matos-soares DNS", check_dns, fatal=False)
print()

# Report
if FATAL:
    print(f"FATAL: Missing env vars: {', '.join(FATAL)}")
    sys.exit(1)
else:
    print("OK: Starting meditation swarm...")
    sys.exit(0)
