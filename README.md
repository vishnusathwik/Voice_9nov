curl -X POST http://localhost:8080/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic dXNlcjpwYXNzd29yZA==" \
  -d '{
    "query": "query { tasks(query: { state: CREATED }) { id name assignee creationDate processInstanceId formKey candidateGroups candidateUsers } }"
  }'
