import requests
import json

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
    
    print("正在发送仓库创建请求...")
    print(f"URL: {url}")
    
    response = requests.post(url, headers=headers, data=json.dumps(data))
    
    print(f"\n响应状态码: {response.status_code}")
    
    if response.status_code == 201:
        print(f"\n仓库创建成功: {response.json()['html_url']}")
        return response.json()['ssh_url']
    elif response.status_code == 422:
        print("仓库已存在，尝试获取现有仓库信息...")
        get_url = f"https://api.github.com/repos/wadexkwd/{repo_name}"
        get_response = requests.get(get_url, headers=headers)
        if get_response.status_code == 200:
            print(f"仓库已存在: {get_response.json()['html_url']}")
            return get_response.json()['ssh_url']
        else:
            print(f"获取仓库信息失败: {get_response.text}")
            return None
    else:
        print(f"\n创建仓库失败: {response.status_code} - {response.text}")
        print("\n请检查令牌是否具有 repo 权限。")
        return None

if __name__ == "__main__":
    TOKEN = input("请输入GitHub个人访问令牌: ")
    REPO_NAME = "stm32-4g-communication-protocol"
    
    ssh_url = create_github_repo(TOKEN, REPO_NAME)
    if ssh_url:
        print(f"\nSSH URL: {ssh_url}")
