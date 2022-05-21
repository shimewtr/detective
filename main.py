import os
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

GITHUB_ACCESS_TOKEN = os.environ['GITHUB_ACCESS_TOKEN']

class Detective():
    def __init__(self):
        organization_name = input("Please enter organization name :")
        team_name = input("Please enter team name :")
        user_name = input("Please enter user name :")

        client = Client(
            transport=RequestsHTTPTransport(
                url = "https://api.github.com/graphql",
                use_json = True,
                headers = {
                    "Content-type": "application/json",
                    "Authorization": "Bearer {}".format(GITHUB_ACCESS_TOKEN)
                },
                retries = 3,
            ),
            fetch_schema_from_transport=True,
        )
        resp = client.execute(
            gql("""
                query($organization_name:String!, $team_name:String!){
                    organization(login:$organization_name) {
                        teams(first: 1, query:$team_name) {
                            nodes {
                                name
                                members(first: 30) {
                                    nodes {
                                        login
                                        contributionsCollection(
                                            from: "2022-04-01T00:00:00+09:00"
                                            to: "2022-05-20T23:59:59+09:00"
                                        ) {
                                            pullRequestContributions(last: 100, orderBy: {direction: ASC}) {
                                                nodes {
                                                    pullRequest {
                                                        title
                                                        url
                                                        additions
                                                        deletions
                                                        state
                                                        commits {
                                                            totalCount
                                                        }
                                                    }
                                                }
                                            }
                                            totalPullRequestContributions
                                            totalCommitContributions
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            """),
            variable_values={
                "organization_name": organization_name,
                "team_name": team_name,
                "user_name": user_name
            })

        print(",".join(["name", "additions", "deletions", "merged_pull_requests", "commits"]))
        for member in resp["organization"]["teams"]["nodes"][0]["members"]["nodes"]:
            login = member["login"]
            additions = 0
            deletions = 0
            merged_pull_requests = 0
            commits = 0
            for pull_request_contributeion in member["contributionsCollection"]["pullRequestContributions"]["nodes"]:
                pull_request = pull_request_contributeion["pullRequest"]
                if True:
                # if pull_request["state"] == "MERGED":
                    additions += pull_request["additions"]
                    deletions += pull_request["deletions"]
                    merged_pull_requests += 1
                    commits += pull_request["commits"]["totalCount"]
            print(",".join([str(n) for n in [login, additions, deletions, merged_pull_requests, commits]]))

if __name__ == '__main__':
    Detective()
