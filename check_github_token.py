import requests
import json

def check_token_scopes(token):
    url = "https://api.github.com/user"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        user_data = response.json()
        print(f"认证成功，用户: {user_data['login']}")
        print(f"用户ID: {user_data['id']}")
        
        # 检查令牌权限
        headers.update({"X-GitHub-Api-Version": "2022-11-28"})
        scopes_response = requests.get("https://api.github.com/rate_limit", headers=headers)
        if scopes_response.status_code == 200:
            if "X-OAuth-Scopes" in scopes_response.headers:
                print(f"令牌权限: {scopes_response.headers['X-OAuth-Scopes']}")
            else:
                print("无法获取令牌权限信息")
        return True
    else:
        print(f"认证失败: {response.status_code} - {response.text}")
        return False

def list_repositories(token):
    url = "https://api.github.com/user/repos"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        repos = response.json()
        print(f"\n用户 {repos[0]['owner']['login']} 的仓库列表:")
        for repo in repos:
            print(f"- {repo['name']} ({repo['html_url']})")
        return repos
    else:
        print(f"获取仓库列表失败: {response.status_code} - {response.text}")
        return []

if __name__ == "__main__":
    TOKEN = input("请输入GitHub个人访问令牌: ")
    
    print("检查GitHub令牌...")
    if check_token_scopes(TOKEN):
        print("\n获取仓库列表...")
        list_repositories(TOKEN)
