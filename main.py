import os
from datetime import datetime, timedelta, timezone
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from tqdm import tqdm

GITHUB_ACCESS_TOKEN = os.environ['GITHUB_ACCESS_TOKEN']

class Detective():
    def __init__(self):
        self.organization_name = input("Organization name        :")
        self.team_name = input("Team name                :")
        user_name = input("[optional]User name      :")
        start_date = input("Start date like 20201231 :")
        end_date = input("End date like 20201231   :")
        start_datetime = datetime.strptime(start_date, '%Y%m%d')
        end_datetime = datetime.strptime(end_date, '%Y%m%d') + timedelta(days=1) - timedelta(seconds=1)
        self.start_datetime_str = start_datetime.strftime("%Y-%m-%dT%H:%M:%S+09:00")
        self.end_datetime_str = end_datetime.strftime("%Y-%m-%dT%H:%M:%S+09:00")
        self.client = self.build_client()

        if user_name:
            contributions = self.summary_member_contributions(user_name)
            self.print_contributions(contributions)
        else:
            members = sorted(self.fetch_members())
            contributions = self.summary_members_contributions(members)
            self.print_contributions(contributions)

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

    def summary_member_contributions(self, member):
        contributions = [["title", "url", "additions", "deletions", "commits"]]

        while True:
            resp = self.fetch_user_contributions(member)
            pull_request_contributions = resp["organization"]["teams"]["nodes"][0]["members"]["nodes"][0]["contributionsCollection"]["pullRequestContributions"]
            page_info = pull_request_contributions["pageInfo"]
            has_next_page = page_info["hasNextPage"]
            for pull_request_contributions in pull_request_contributions["nodes"]:
                pull_request = pull_request_contributions["pullRequest"]
                if pull_request["state"] == "MERGED":
                    title = pull_request["title"].replace(',', '')
                    url = pull_request["url"]
                    additions = pull_request["additions"]
                    deletions = pull_request["deletions"]
                    commits = pull_request["commits"]["totalCount"]
                    contributions.append([title, url, additions, deletions, commits])
            if not has_next_page:
                break
        return contributions


    def summary_members_contributions(self, members):
        contributions = [["name", "additions", "deletions", "merged_pull_requests", "commits"]]
        for member in tqdm(members):
            name = member
            additions = 0
            deletions = 0
            merged_pull_requests = 0
            commits = 0
            after = None

            while True:
                resp = self.fetch_user_contributions(member, after=after)
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

    def fetch_user_contributions(self, member, after=None):
        resp = self.client.execute(
                    gql("""
                        query($organization_name:String!, $team_name:String!, $member:String!, $after:String, $start_datetime:DateTime!, $end_datetime:DateTime!){
                            organization(login:$organization_name) {
                                teams(first: 1, query:$team_name) {
                                    nodes {
                                        name
                                        members(first: 1, query:$member) {
                                            nodes {
                                                login
                                                contributionsCollection(
                                                    from: $start_datetime
                                                    to: $end_datetime
                                                ) {
                                                    pullRequestContributions(first: 100 after:$after) {
                                                        pageInfo {
                                                            hasNextPage
                                                            endCursor
                                                        }
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
                        "organization_name": self.organization_name,
                        "team_name": self.team_name,
                        "member": member,
                        "after": after,
                        "start_datetime": self.start_datetime_str,
                        "end_datetime": self.end_datetime_str,
                    })
        return resp

    def print_contributions(self, contributions):
        for contribution in contributions:
            print(",".join([str(i) for i in contribution]))


if __name__ == '__main__':
    Detective()
