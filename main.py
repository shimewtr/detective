import os
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

GITHUB_ACCESS_TOKEN = os.environ['GITHUB_ACCESS_TOKEN']

class Detective():
    def __init__(self):
        organization_name = input("Please enter organization name :")
        team_name = input("Please enter team name :")
        user_name = input("Please enter user name :")

        self.client = Client(
        self.client = self.build_client()
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
