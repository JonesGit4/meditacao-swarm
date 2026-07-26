#!/usr/bin/env python3
"""
Pre-Build Validation for Meditacao Swarm.
Tests all critical connections BEFORE deploy.
Usage: python3 scripts/prebuild_check.py
"""
import os, sys, json, time, urllib.request, urllib.error

ALL_OK = True

def test(name, fn):
    global ALL_OK
    start = time.time()
    try:
        result = fn()
        elapsed = time.time() - start
        status = "PASS" if result else "FAIL"
        print(f"  [{status}] {name} ({elapsed:.1f}s)")
        if not result:
            ALL_OK = False
        return result
    except Exception as e:
        elapsed = time.time() - start
        print(f"  [FAIL] {name} ({elapsed:.1f}s) -> {e}")
        ALL_OK = False
        return False

print("Meditacao Swarm - Pre-Build Validation")
print(f"{time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
print()

# 1. DeepSeek API
DS_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DS_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-pro")
DS_BASE = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")

def check_deepseek():
    data = json.dumps({
        "model": DS_MODEL,
        "messages": [{"role": "user", "content": "Responda apenas: OK"}],
        "max_tokens": 5,
        "temperature": 0
    }).encode()
    req = urllib.request.Request(f"{DS_BASE}/chat/completions", data=data,
        headers={"Authorization": f"Bearer {DS_KEY}", "Content-Type": "application/json"})
    resp = json.loads(urllib.request.urlopen(req, timeout=15).read())
    return "OK" in resp["choices"][0]["message"]["content"]

print("1. DeepSeek API")
test(f"Model {DS_MODEL} + API key", check_deepseek)
print()

# 2. Internal Services
print("2. Internal Services (Swarm network)")
def check_matos_dns():
    import socket
    socket.gethostbyname("matos-soares")
    return True
test("matos-soares DNS", check_matos_dns)
print()

# 3. Baserow
def check_baserow():
    token = os.environ.get("BASEROW_TOKEN", "")
    if not token:
        return False
    req = urllib.request.Request(
        "https://base.duobro.com.br/api/database/rows/table/828/?user_field_names=true&size=1",
        headers={"Authorization": f"Token {token}"})
    resp = json.loads(urllib.request.urlopen(req, timeout=10).read())
    return "count" in resp

print("3. Baserow")
test("Table 828 (Meditacoes)", check_baserow)
print()

if ALL_OK:
    print("PASS: All checks OK - safe to deploy.")
    sys.exit(0)
else:
    print("FAIL: Some checks failed - DO NOT deploy!")
    sys.exit(1)
