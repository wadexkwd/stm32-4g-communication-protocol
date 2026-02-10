import requests
import json
from datetime import datetime

def create_github_repo(token, repo_name, description="STM32 4G Communication Protocol Project"):
    url = "https://api.github.com/user/repos"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "name": repo_name,
        "description": description,
        "private": False,
        "auto_init": False
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(data))
    
    if response.status_code == 201:
        print(f"仓库创建成功: {response.json()['html_url']}")
        return response.json()['ssh_url']  # 返回SSH URL用于后续操作
    elif response.status_code == 422:
        print("仓库已存在，尝试获取现有仓库信息...")
        # 尝试获取现有仓库的SSH URL
        get_url = f"https://api.github.com/repos/wadexkwd/{repo_name}"
        get_response = requests.get(get_url, headers=headers)
        if get_response.status_code == 200:
            print(f"仓库已存在: {get_response.json()['html_url']}")
            return get_response.json()['ssh_url']
        else:
            print(f"获取仓库信息失败: {get_response.text}")
            return None
    else:
        print(f"创建仓库失败: {response.status_code} - {response.text}")
        return None

if __name__ == "__main__":
    TOKEN = input("请输入GitHub个人访问令牌: ")
    REPO_NAME = "stm32-4g-communication-protocol"
    
    ssh_url = create_github_repo(TOKEN, REPO_NAME)
    if ssh_url:
        print(f"SSH URL: {ssh_url}")
