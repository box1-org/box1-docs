#!/bin/sh
# Local Keycloak realm box1 for run 19 (test-only), shaped like the proposed cluster clients (D-009):
#  - client inventory-service with client role inventory-admin;
#  - confidential client scenario-controller: its service account holds inventory-service/inventory-admin, and audience
#    mappers add inventory-service and scenario-controller; client roles scenario-operator and scenario-viewer; direct
#    grants on (local only, so test users get tokens without a browser);
#  - users operator (scenario-operator), viewer (scenario-viewer), norole.
# Secrets are generated into the scratch WORK directory and never printed or committed.
set -eu
WORK=/private/tmp/claude-501/-Users-mike-Documents-ChatGPT-box1/ef05c591-4bf3-4f8d-9761-3715c9f2aabb/scratchpad/run19-work
KC=http://localhost:39180/auth
[ -s "$WORK/client-secret" ] || openssl rand -hex 24 > "$WORK/client-secret"
[ -s "$WORK/user-password" ] || openssl rand -hex 16 > "$WORK/user-password"
ADMIN=$(curl -sf -d grant_type=password -d client_id=admin-cli -d username=admin -d "password=$(cat "$WORK/kc-admin")" \
  "$KC/realms/master/protocol/openid-connect/token" | python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')
api() { curl -sf -X "$1" -H "Authorization: Bearer $ADMIN" -H 'Content-Type: application/json' "$KC/admin/realms$2" ${3:+--data "$3"}; }
first_id() { python3 -c 'import json,sys; print(json.load(sys.stdin)[0]["id"])'; }
api POST "" '{"realm":"box1","enabled":true}'
api POST /box1/clients '{"clientId":"inventory-service","enabled":true,"publicClient":false,"standardFlowEnabled":false,"directAccessGrantsEnabled":false,"serviceAccountsEnabled":false}'
api POST /box1/clients "{\"clientId\":\"scenario-controller\",\"enabled\":true,\"publicClient\":false,\"secret\":\"$(cat "$WORK/client-secret")\",\"standardFlowEnabled\":false,\"directAccessGrantsEnabled\":true,\"serviceAccountsEnabled\":true,\"protocolMappers\":[{\"name\":\"inventory-audience\",\"protocol\":\"openid-connect\",\"protocolMapper\":\"oidc-audience-mapper\",\"config\":{\"included.client.audience\":\"inventory-service\",\"access.token.claim\":\"true\"}},{\"name\":\"own-audience\",\"protocol\":\"openid-connect\",\"protocolMapper\":\"oidc-audience-mapper\",\"config\":{\"included.client.audience\":\"scenario-controller\",\"access.token.claim\":\"true\"}}]}"
INV=$(api GET "/box1/clients?clientId=inventory-service" | first_id)
SC=$(api GET "/box1/clients?clientId=scenario-controller" | first_id)
api POST "/box1/clients/$INV/roles" '{"name":"inventory-admin"}'
api POST "/box1/clients/$SC/roles" '{"name":"scenario-operator"}'
api POST "/box1/clients/$SC/roles" '{"name":"scenario-viewer"}'
SA=$(api GET "/box1/clients/$SC/service-account-user" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')
role() { api GET "/box1/clients/$1/roles/$2"; }
api POST "/box1/users/$SA/role-mappings/clients/$INV" "[$(role "$INV" inventory-admin)]"
for u in operator viewer norole; do
  api POST /box1/users "{\"username\":\"$u\",\"enabled\":true,\"email\":\"$u@run19.invalid\",\"emailVerified\":true,\"firstName\":\"$u\",\"lastName\":\"run19\",\"credentials\":[{\"type\":\"password\",\"value\":\"$(cat "$WORK/user-password")\",\"temporary\":false}]}"
done
uid() { api GET "/box1/users?username=$1&exact=true" | first_id; }
api POST "/box1/users/$(uid operator)/role-mappings/clients/$SC" "[$(role "$SC" scenario-operator)]"
api POST "/box1/users/$(uid viewer)/role-mappings/clients/$SC" "[$(role "$SC" scenario-viewer)]"
echo "realm box1 ready (clients inventory-service, scenario-controller; users operator, viewer, norole)"
