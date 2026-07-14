import urllib.request
import urllib.parse
import json
import sys
import time

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
    if len(sys.argv) < 2:
        print("[ERROR] Render API Key is required.")
        print("Usage: python deploy_render.py <RENDER_API_KEY>")
        sys.exit(1)
        
    api_key = sys.argv[1]
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
    
    repo_url = "https://github.com/The-AI-Aces/MirrorAnalysier.git"
    service_name = "mirror-analyzer"
    
    # Check if a service with this name already exists
    print("Checking if service already exists...")
    status, services = make_request("https://api.render.com/v1/services?limit=20", headers=headers)
    existing_service = None
    if status == 200:
        for s in services:
            if s['service']['name'] == service_name:
                existing_service = s['service']
                break
                
    if existing_service:
        service_id = existing_service['id']
        live_url = existing_service['url']
        print(f"Service '{service_name}' already exists (ID: {service_id}). URL: {live_url}")
        print("Triggering a new deployment to push the latest TFLite changes...")
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
        print(f"Creating new Web Service '{service_name}' on Render...")
        service_body = {
            "type": "web_service",
            "name": service_name,
            "ownerId": owner_id,
            "repo": repo_url,
            "branch": "main",
            "autoDeploy": "yes",
            "serviceDetails": {
                "env": "python",
                "buildCommand": "pip install -r requirements.txt",
                "startCommand": "python app_medical.py",
                "planId": "free"
            }
        }
        status, create_res = make_request(
            "https://api.render.com/v1/services",
            method="POST",
            headers=headers,
            body=service_body
        )
        if status not in [200, 201]:
            print(f"Error creating Web Service: {create_res}")
            sys.exit(1)
            
        service_id = create_res['service']['id']
        live_url = create_res['service']['url']
        print(f"Web Service created successfully (ID: {service_id})!")
        print(f"Service Live URL will be: {live_url}")

    # Poll deployment status
    print("\nMonitoring deployment status...")
    print("This usually takes 2-4 minutes on the Render free tier. Please wait...")
    
    start_time = time.time()
    last_status = None
    
    while True:
        # Prevent infinite polling
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
