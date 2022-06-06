import os
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from tqdm import tqdm

GITHUB_ACCESS_TOKEN = os.environ['GITHUB_ACCESS_TOKEN']

class Detective():
    def __init__(self):
        organization_name = input("Please enter organization name :")
        team_name = input("Please enter team name :")
        user_name = input("Please enter user name :")

        self.client = Client(
        self.client = self.build_client()
        contributions = self.fetch_contributions()
    def build_client(self):
        return Client(
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
        self.members = self.fetch_members()
        print(self.members)

    def fetch_contributions(self):
        contributions = ["name", "additions", "deletions", "merged_pull_requests", "commits"]
        for member in tqdm(self.members):
            name = member
            additions = 0
            deletions = 0
            merged_pull_requests = 0
            commits = 0
            after = None

            while True:
                resp = self.client.execute(
                    gql("""
                        query($organization_name:String!, $team_name:String!, $member:String!, $after:String){
                            organization(login:$organization_name) {
                                teams(first: 1, query:$team_name) {
                                    nodes {
                                        name
                                        members(first: 1, query:$member) {
                                            nodes {
                                                login
                                                contributionsCollection(
                                                    from: "2022-04-01T00:00:00+09:00"
                                                    to: "2022-05-25T23:59:59+09:00"
                                                ) {
                                                    pullRequestContributions(first: 100 after:$after) {
                                                        pageInfo {
                                                            hasNextPage
                                                            endCursor
                                                        }
                                                        nodes {
                                                            pullRequest {
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
                        "organization_name": self.organization_name,
                        "team_name": self.team_name,
                        "member": member,
                        "after": after
                    })
                pull_request_contributions = resp["organization"]["teams"]["nodes"][0]["members"]["nodes"][0]["contributionsCollection"]["pullRequestContributions"]
                page_info = pull_request_contributions["pageInfo"]
                after = page_info["endCursor"]
                has_next_page = page_info["hasNextPage"]
                for pull_request_contributions in pull_request_contributions["nodes"]:
                    pull_request = pull_request_contributions["pullRequest"]
                    if pull_request["state"] == "MERGED":
                        additions += pull_request["additions"]
                        deletions += pull_request["deletions"]
                        merged_pull_requests += 1
                        commits += pull_request["commits"]["totalCount"]
                if not has_next_page:
                    break
            contributions.append([name, additions, deletions, merged_pull_requests, commits])
        return contributions

    def fetch_members(self):
        members = []
        after = None
        while True:
            resp = self.client.execute(
                gql("""
                    query($organization_name:String!, $team_name:String!, $after:String){
                        organization(login:$organization_name) {
                            teams(first: 1, query:$team_name) {
                                nodes {
                                    name
                                    members(first: 100 after:$after) {
                                        pageInfo {
                                            hasNextPage
                                            endCursor
                                        }
                                        nodes {
                                            login
                                        }
                                    }
                                }
                            }
                        }
                    }
                """),
                variable_values={
                    "organization_name": self.organization_name,
                    "team_name": self.team_name,
                    "after": after
                })
            page_info = resp["organization"]["teams"]["nodes"][0]["members"]["pageInfo"]
            after = page_info["endCursor"]
            has_next_page = page_info["hasNextPage"]
            for member in resp["organization"]["teams"]["nodes"][0]["members"]["nodes"]:
                members.append(member["login"])
            if not has_next_page:
                break
        return members

if __name__ == '__main__':
    Detective()
