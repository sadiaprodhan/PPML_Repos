import requests
from dateutil.parser import parse
import urllib
import json


privacy_libraries = ['pysyft', 'opacus', 'tensorflow_privacy', 'tenseal']
selected_repos= []
lib_repo_counts = []

def commit_count(project):
    url = f'https://api.github.com/repos/{project}/commits'
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': 'token ' + token
    }
    params = {
        
        'per_page': 1,
    }
    resp = requests.request('GET', url, params=params,headers=headers)
    if (resp.status_code // 100) != 2:
        raise Exception(f'invalid github response: {resp.content}')
    # check the resp count, just in case there are 0 commits
    commit_count = len(resp.json())
    last_page = resp.links.get('last')
    # if there are no more pages, the count must be 0 or 1
    if last_page:
        # extract the query string from the last page url
        qs = urllib.parse.urlparse(last_page['url']).query
        # extract the page number from the query string
        commit_count = int(dict(urllib.parse.parse_qsl(qs))['page'])
    return commit_count


def getResponse(url):
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': 'token ' + token
    }
  
    response = requests.get(url, headers=headers)
    return response
   
def parseResultsOfSearch(response):
    projects_response = response.json()
    projects_list = projects_response["items"]
    for i in range(len(projects_list)):
        per_project_dict = projects_list[i]
        
        existing_repo = next((item for item in selected_repos if item["full_name"] ==  f'{per_project_dict["repository"]["full_name"]}'), None)
        if existing_repo == None:
            repo_search_url = f'https://api.github.com/repos/{per_project_dict["repository"]["full_name"]}'
            repo_response = getResponse(repo_search_url)
            repo_dict= repo_response.json()
          
            if repo_dict["private"] == False:
                creation_Date = parse(repo_dict["created_at"])
                pushed_Date = parse(repo_dict["pushed_at"])
                if((pushed_Date - creation_Date).days > 180):
                    commits = commit_count(repo_dict["full_name"])
                    if(commits) > 5 :
                        if(repo_dict["stargazers_count"] > 10):
                            dict = {"full_name": repo_dict["full_name"], "repo_name": repo_dict["name"], "star_count": repo_dict["stargazers_count"], "commits_count": commits, "creation_date": repo_dict["created_at"], "last_commit_date": repo_dict["pushed_at"]}
                            selected_repos.append(dict)      
                            

    
def find_counts():
    for lib in privacy_libraries:
        with open(f'{lib}.json') as repo_files:
            file_contents = json.loads(repo_files.read())   
            count = len(file_contents)
            dict = {"library": lib, "repo_count": count}
            lib_repo_counts.append(dict)
    with open('repo_counts.json', 'w') as file:
            json.dump(lib_repo_counts,file)
    
        




def findRepos():
    for lib in privacy_libraries:
        url = f'https://api.github.com/search/code?q={lib}+in:file +language:python&sort=stars&direction=desc'
        response = getResponse(url)
        print(response)
        parseResultsOfSearch(response)
        print(len(selected_repos))
        while len(selected_repos) <= 20:
            url = response.links.get("next")
            if url != None:
                url = url["url"]
                print(url)
    
                response = getResponse(url)
                parseResultsOfSearch(response)
                print(len(selected_repos))
            else:
                break
    
        with open(f'{lib}.json', 'w') as file:
            json.dump(selected_repos,file)
        selected_repos.clear()

if __name__ == "__main__":
    token = ''
    with open('token.txt', 'r') as file:
        token = file.read()
       
    #findRepos()
    find_counts()

  
