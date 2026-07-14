import urllib.request
import urllib.parse
import json
import sys
import time
import os

def make_request(url, method="GET", headers=None, body=None):
    if headers is None:
        headers = {}
    
    data = None
    if body is not None:
        data = json.dumps(body).encode('utf-8')
        headers["Content-Type"] = "application/json"
    
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as res:
            return res.status, json.loads(res.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        try:
            err_data = json.loads(e.read().decode('utf-8'))
        except:
            err_data = e.reason
        return e.code, err_data
    except Exception as e:
        return 0, str(e)

def main():
    api_key = None
    if len(sys.argv) >= 2:
        api_key = sys.argv[1]
    else:
        # Load from ~/.env
        env_path = os.path.expanduser("~/.env")
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                for line in f:
                    if line.strip().startswith("RENDER_API_KEY="):
                        api_key = line.split("=", 1)[1].strip()
                        break
                        
    if not api_key:
        print("[ERROR] Render API Key not found. Please provide it as a CLI argument or save it to ~/.env")
        print("Usage: python deploy_render.py <RENDER_API_KEY>")
        sys.exit(1)
        
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json"
    }
    
    print("Fetching Render owner ID...")
    status, owners = make_request("https://api.render.com/v1/owners", headers=headers)
    if status != 200:
        print(f"Error fetching owners (Status {status}): {owners}")
        sys.exit(1)
        
    if not owners:
        print("No owners found in Render account.")
        sys.exit(1)
        
    owner_id = owners[0]['owner']['id']
    owner_name = owners[0]['owner']['name']
    print(f"Authenticated successfully as: {owner_name} (ID: {owner_id})")
    
    repo_url = "https://github.com/The-AI-Aces/MirrorAnalysier"
    repo_url_git = repo_url + ".git"
    
    # Check if a service with this name or repo already exists
    print("Checking if service already exists...")
    status, services = make_request("https://api.render.com/v1/services?limit=50", headers=headers)
    existing_service = None
    if status == 200:
        for s in services:
            svc = s['service']
            name_match = svc['name'].lower() in ["mirror-analyzer", "mirroranalysier"]
            repo_match = svc['repo'].lower() in [repo_url.lower(), repo_url_git.lower()]
            if name_match or repo_match:
                existing_service = svc
                break
                
    if existing_service:
        service_id = existing_service['id']
        live_url = existing_service.get('url', '') or existing_service.get('serviceDetails', {}).get('url', '')
        print(f"Service matched (ID: {service_id}). URL: {live_url}")
        
        # Make sure the start command and build commands are correct!
        print("Updating build and start commands for TFLite compatibility...")
        patch_body = {
            "serviceDetails": {
                "envSpecificDetails": {
                    "buildCommand": "pip install -r requirements.txt",
                    "startCommand": "python app_medical.py"
                }
            }
        }
        update_status, update_res = make_request(
            f"https://api.render.com/v1/services/{service_id}",
            method="PATCH",
            headers=headers,
            body=patch_body
        )
        if update_status == 200:
            print("Successfully updated service start/build commands.")
        else:
            print(f"Warning: Failed to update commands via API: {update_res}")

        # Update environment variables to pin Python version
        print("Updating Render environment variables to set PYTHON_VERSION=3.11.11...")
        env_status, env_vars = make_request(f"https://api.render.com/v1/services/{service_id}/env-vars", headers=headers)
        if env_status == 200:
            vars_list = [v['envVar'] for v in env_vars]
            found = False
            for v in vars_list:
                if v['key'] == 'PYTHON_VERSION':
                    v['value'] = '3.11.11'
                    found = True
                    break
            if not found:
                vars_list.append({'key': 'PYTHON_VERSION', 'value': '3.11.11'})
            
            # Put env vars back
            put_status, put_res = make_request(
                f"https://api.render.com/v1/services/{service_id}/env-vars",
                method="PUT",
                headers=headers,
                body=vars_list
            )
            if put_status == 200:
                print("Successfully updated environment variables.")
            else:
                print(f"Warning: Failed to set environment variables: {put_res}")

        print("Triggering a new deployment to push the latest changes...")
        deploy_status, deploy_res = make_request(
            f"https://api.render.com/v1/services/{service_id}/deploys",
            method="POST",
            headers=headers,
            body={}
        )
        if deploy_status not in [200, 201]:
            print(f"Failed to trigger deploy: {deploy_res}")
            sys.exit(1)
    else:
        print("[ERROR] Service does not exist. Please create the service manually on Render first to avoid payment checks.")
        sys.exit(1)

    # Poll deployment status
    print("\nMonitoring deployment status...")
    print("This usually takes 2-4 minutes on the Render free tier. Please wait...")
    
    start_time = time.time()
    last_status = None
    
    while True:
        if time.time() - start_time > 600: # 10 minutes timeout
            print("\n[TIMEOUT] Deployment monitoring timed out. The build may still be running on Render.")
            print(f"Please check the Render Dashboard: https://dashboard.render.com/web/{service_id}")
            print(f"Your live URL will be: {live_url}")
            sys.exit(0)
            
        status, deploys = make_request(f"https://api.render.com/v1/services/{service_id}/deploys?limit=5", headers=headers)
        if status != 200 or not deploys:
            time.sleep(15)
            continue
            
        latest_deploy = deploys[0]['deploy']
        deploy_status = latest_deploy['status']
        
        if deploy_status != last_status:
            print(f"[{time.strftime('%H:%M:%S')}] Deploy status: {deploy_status.upper()}")
            last_status = deploy_status
            
        if deploy_status == "live":
            print("\n" + "="*60)
            print("🎉 DEPLOYMENT SUCCESSFUL!")
            print("="*60)
            print(f"Render Dashboard URL: https://dashboard.render.com/web/{service_id}")
            print(f"Live Working URL    : {live_url}")
            print("="*60 + "\n")
            sys.exit(0)
        elif deploy_status in ["failed", "canceled"]:
            print(f"\n[ERROR] Deployment failed with status: {deploy_status.upper()}")
            print(f"Check build logs on Render: https://dashboard.render.com/web/{service_id}")
            sys.exit(1)
            
        time.sleep(15)

if __name__ == "__main__":
    main()
