import os
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

GITHUB_ACCESS_TOKEN = os.environ['GITHUB_ACCESS_TOKEN']

class Detective():
    def __init__(self):
        access_token = GITHUB_ACCESS_TOKEN
        client = Client(
            transport=RequestsHTTPTransport(
                url = "https://api.github.com/graphql",
                use_json = True,
                headers = {
                    "Content-type": "application/json",
                    "Authorization": "Bearer {}".format(access_token)
                },
                retries = 3,
            ),
            fetch_schema_from_transport=True,
        )
        resp = client.execute(
            gql("""
                query($owner:String!, $name:String!) {
                    repository(owner:$owner, name:$name){
                        pullRequests(first:100, states:OPEN) {
                    nodes { number }
                    }
                }
            }"""),
            variable_values={
                "owner": "shimewtr",
                "name": "anopost"
            })

        for pr in resp['repository']['pullRequests']['nodes']:
            print(pr['number'])

if __name__ == '__main__':
    Detective()
