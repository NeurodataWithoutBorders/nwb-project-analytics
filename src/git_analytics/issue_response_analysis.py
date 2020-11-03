API_KEY = ""  # generic GitHub API key

DEV_USERNAMES = (  # issues raised by core devs are excluded from analysis
    'rly',
    'bendichter',
    'oruebel',
    'ajtritt',
    'ln-vidrio',
    't-b'
)

REPOS = (
    "NeurodataWithoutBorders/pynwb",
    "hdmf-dev/hdmf",
    "NeurodataWithoutBorders/nwb-schema",
    "NeurodataWithoutBorders/matnwb"
)

START = datetime(2019, 11, 1)

g = Github(API_KEY)

df_dict = defaultdict(list)


for repo in tqdm(REPOS, position=0, desc='repos'):    
    all_issues = g.get_repo(repo).get_issues(since=START)
    for issue in tqdm(all_issues, position=1, total=all_issues.totalCount, desc='issues'):
        if issue.user.login not in DEV_USERNAMES and issue.pull_request is None:
            df_dict['repo'].append(repo)
            df_dict['issue_number'].append(issue.number)
            df_dict['created_time'].append(issue.created_at)
            
            df_dict['response_time'].append(pd.NaT)  # left as pd.NaT if no comments and not self-closed
            
            if issue.comments:
                for comment in issue.get_comments():
                    if issue.user != comment.user:  # don't count it if the user commented on their own issue
                        df_dict['response_time'][-1] = comment.created_at
                        continue
            if issue.closed_by == issue.user:  # if user closes their own issue, count it as resolved
                df_dict['response_time'][-1] = np.min([df_dict['response_time'][-1], issue.closed_at])
                
                
df = pd.DataFrame(df_dict)
df.to_csv('issue_responses.csv')


## ANALYSIS
med_resp_time = np.median([x for x in (df['response_time'] - df['created_time']) if not pd.isna(x)])
print('median response time: {}'.format(med_resp_time))

unresponded = df[['repo','issue_number']][pd.isna(df['response_time'])]
print('unresponded issues ({}):'.format(len(unresponded)))
print(unresponded)
