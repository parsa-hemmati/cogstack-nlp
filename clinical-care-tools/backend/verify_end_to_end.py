import sys
import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"

def run_test():
    print("Starting E2E API Verification...")
    
    # 1. Login
    print("1. Logging in...")
    try:
        resp = requests.post(f"{BASE_URL}/auth/login", json={"username": "admin", "password": "StrongAdminPass1!"}, timeout=10)
    except Exception as e:
        print(f"Connection failed: {e}")
        sys.exit(1)

    if resp.status_code != 200:
        print(f"Login failed: {resp.status_code} {resp.text}")
        sys.exit(1)
    
    data = resp.json()
    token = data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("   Login successful. Token acquired.")

    # 2. Create Project
    print("2. Creating Project...")
    project_payload = {"name": "Sepsis Verification Project", "description": "Automated test project"}
    resp = requests.post(f"{BASE_URL}/projects", json=project_payload, headers=headers)
    
    if resp.status_code not in [200, 201]:
        print(f"Create Project failed: {resp.status_code} {resp.text}")
        sys.exit(1)
        
    project = resp.json()
    project_id = project["id"]
    print(f"   Project created: {project_id}")

    # 3. Upload Document
    print("3. Uploading 'sepsis_note.rtf'...")
    try:
        files = {
            'file': ('sepsis_note.rtf', open('mock_data/sepsis_note.rtf', 'rb'), 'application/rtf')
        }
    except FileNotFoundError:
        print("Error: Mock data file not found inside container path.")
        sys.exit(1)

    data = {'project_id': project_id}
    
    resp = requests.post(f"{BASE_URL}/documents/upload", headers=headers, files=files, data=data) 
    
    if resp.status_code not in [200, 201]:
        print(f"Upload failed: {resp.status_code} {resp.text}")
        sys.exit(1)
        
    doc = resp.json()
    doc_id = doc["document_id"]
    print(f"   Document uploaded successfully: {doc_id}")
    print(f"   Processing Status: {doc['status']}")

    print("\nE2E Verification PASSED!")

if __name__ == "__main__":
    run_test()
