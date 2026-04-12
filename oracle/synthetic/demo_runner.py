import os
import time
import json
import requests
from dotenv import load_dotenv

from .synthetic_generator import create_demo_cycle

load_dotenv()

ORACLE_BASE = os.getenv("ORACLE_BASE_URL", "http://127.0.0.1:8001")
RPC_URL = os.getenv("WEB3_PROVIDER_URL", "http://127.0.0.1:8545")

FRONTEND_ENV = os.path.expanduser("~/Projects/MsmeFundingPlatform/frontend/.env")


def rpc(method, params=None):
    params = params or []
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    r = requests.post(RPC_URL, json=payload, timeout=5)
    r.raise_for_status()
    return r.json()


def load_contract_addresses():
    addrs = []
    if not os.path.exists(FRONTEND_ENV):
        return addrs
    with open(FRONTEND_ENV, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if line.startswith("VITE_") and "CONTRACT" in line and "=" in line:
                _, val = line.split("=", 1)
                val = val.strip()
                if val.startswith("0x") and len(val) == 42:
                    addrs.append(val)
    return addrs


def api_smoke():
    ok = True
    try:
        r = requests.get(f"{ORACLE_BASE}/openapi.json", timeout=5)
        r.raise_for_status()
        spec = r.json()
        paths = spec.get("paths", {})
        test_paths = []
        for pth, methods in paths.items():
            if "{" in pth:
                continue
            if "get" in methods:
                test_paths.append(pth)
        test_paths = test_paths[:10]

        for pth in test_paths:
            url = f"{ORACLE_BASE}{pth}"
            rr = requests.get(url, timeout=5)
            if rr.status_code in (200, 401, 403, 404):
                continue
            ok = False
            print("API unexpected status", rr.status_code, "for", url)
    except Exception as e:
        ok = False
        print("API smoke error:", e)
    return ok


def blockchain_smoke():
    ok = True
    try:
        chain_id = rpc("eth_chainId")["result"]
        block = rpc("eth_blockNumber")["result"]
        print("chainId", chain_id, "block", block)
        for addr in load_contract_addresses():
            code = rpc("eth_getCode", [addr, "latest"]).get("result", "0x")
            if code == "0x":
                ok = False
                print("Missing contract code at", addr)
    except Exception as e:
        ok = False
        print("Blockchain smoke error:", e)
    return ok


def main():
    interval = int(os.getenv("DEMO_INTERVAL", "60"))
    while True:
        print("=== DEMO CYCLE START ===")
        create_demo_cycle(verbose=True)
        api_ok = api_smoke()
        bc_ok = blockchain_smoke()
        print("API_OK", api_ok, "BLOCKCHAIN_OK", bc_ok)
        print("=== DEMO CYCLE END ===")
        time.sleep(interval)


if __name__ == "__main__":
    main()
