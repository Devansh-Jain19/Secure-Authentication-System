import urllib.request
import json

def test_full_flow():
    base_url = "http://localhost:5000/api"
    
    # 1. Test Health
    req = urllib.request.Request(f"{base_url}/health")
    with urllib.request.urlopen(req) as resp:
        health_data = json.loads(resp.read().decode())
        print("[1] HEALTH CHECK:", json.dumps(health_data, indent=2))
        
    # 2. Test Login
    login_payload = json.dumps({
        "identifier": "alice_dev",
        "password": "SuperSecretPassword123!"
    }).encode("utf-8")
    
    req = urllib.request.Request(f"{base_url}/auth/login", data=login_payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        login_res = json.loads(resp.read().decode())
        print("\n[2] LOGIN SUCCESSFUL! USER:", login_res["user"]["username"], "| ROLE:", login_res["user"]["role"])
        access_token = login_res["tokens"]["access_token"]
        refresh_token = login_res["tokens"]["refresh_token"]
        print("Generated JWT Access Token:", access_token[:40] + "...")
        
    # 3. Test Protected Profile Route with JWT
    req = urllib.request.Request(f"{base_url}/auth/profile", headers={"Authorization": f"Bearer {access_token}"})
    try:
        with urllib.request.urlopen(req) as resp:
            prof_res = json.loads(resp.read().decode())
            print("\n[3] PROTECTED PROFILE ACCESS SUCCESSFUL:")
            print(json.dumps(prof_res, indent=2))
    except urllib.error.HTTPError as e:
        print("\n[3] PROFILE FAILED:", e.code, e.read().decode())

    # 4. Test Token Refresh
    refresh_payload = json.dumps({"refresh_token": refresh_token}).encode("utf-8")
    req = urllib.request.Request(f"{base_url}/auth/refresh", data=refresh_payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        ref_res = json.loads(resp.read().decode())
        print("\n[4] REFRESH TOKEN ROTATION SUCCESSFUL:")
        print("New Access Token:", ref_res["tokens"]["access_token"][:40] + "...")

    # 5. Test Admin Protected Route (Audit logs)
    req = urllib.request.Request(f"{base_url}/admin/users", headers={"Authorization": f"Bearer {access_token}"})
    with urllib.request.urlopen(req) as resp:
        admin_res = json.loads(resp.read().decode())
        print(f"\n[5] ADMIN AUDIT LOGS RETRIEVED ({len(admin_res['audit_logs'])} events captured):")
        for log in admin_res["audit_logs"][:3]:
            print(f" - [{log['created_at']}] User '{log['username']}': {log['event_type']} from {log['ip_address']}")

if __name__ == "__main__":
    test_full_flow()
