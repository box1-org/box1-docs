#!/bin/sh
# Adds the operations-console client to run 19's local realm box1 (test-only), shaped like the proposed box1-gitops
# change: public, code flow with PKCE S256, fullScopeAllowed false, audience mappers for operations-console and
# scenario-controller, and scope mappings for its own console-* roles and scenario-controller's scenario-* roles.
# Users (from realm.sh): operator = console-operator + scenario-operator; viewer = console-viewer + scenario-viewer;
# norole = console-operator only (so the scenario controller refuses it).
set -eu
WORK=/private/tmp/claude-501/-Users-mike-Documents-ChatGPT-box1/ef05c591-4bf3-4f8d-9761-3715c9f2aabb/scratchpad/run19-work
KC=http://localhost:39180/auth
CONSOLE=http://localhost:39085
ADMIN=$(curl -sf -d grant_type=password -d client_id=admin-cli -d username=admin -d "password=$(cat "$WORK/kc-admin")" \
  "$KC/realms/master/protocol/openid-connect/token" | python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')
api() { curl -sf -X "$1" -H "Authorization: Bearer $ADMIN" -H 'Content-Type: application/json' "$KC/admin/realms$2" ${3:+--data "$3"}; }
first_id() { python3 -c 'import json,sys; print(json.load(sys.stdin)[0]["id"])'; }
aud() { printf '{"name":"%s-audience","protocol":"openid-connect","protocolMapper":"oidc-audience-mapper","config":{"included.client.audience":"%s","access.token.claim":"true","id.token.claim":"false"}}' "$1" "$1"; }
api POST /box1/clients "{\"clientId\":\"operations-console\",\"enabled\":true,\"publicClient\":true,\"standardFlowEnabled\":true,\"implicitFlowEnabled\":false,\"directAccessGrantsEnabled\":false,\"fullScopeAllowed\":false,\"redirectUris\":[\"$CONSOLE/callback\",\"$CONSOLE/signed-out.html\"],\"webOrigins\":[\"$CONSOLE\"],\"attributes\":{\"pkce.code.challenge.method\":\"S256\",\"post.logout.redirect.uris\":\"$CONSOLE/signed-out.html\"},\"protocolMappers\":[$(aud operations-console),$(aud scenario-controller)]}"
OC=$(api GET "/box1/clients?clientId=operations-console" | first_id)
SC=$(api GET "/box1/clients?clientId=scenario-controller" | first_id)
for r in console-viewer console-operator console-developer; do api POST "/box1/clients/$OC/roles" "{\"name\":\"$r\"}"; done
role() { api GET "/box1/clients/$1/roles/$2"; }
api POST "/box1/clients/$OC/scope-mappings/clients/$OC" "[$(role "$OC" console-viewer),$(role "$OC" console-operator),$(role "$OC" console-developer)]"
api POST "/box1/clients/$OC/scope-mappings/clients/$SC" "[$(role "$SC" scenario-viewer),$(role "$SC" scenario-operator)]"
uid() { api GET "/box1/users?username=$1&exact=true" | first_id; }
api POST "/box1/users/$(uid operator)/role-mappings/clients/$OC" "[$(role "$OC" console-operator)]"
api POST "/box1/users/$(uid viewer)/role-mappings/clients/$OC" "[$(role "$OC" console-viewer)]"
api POST "/box1/users/$(uid norole)/role-mappings/clients/$OC" "[$(role "$OC" console-operator)]"
echo "client operations-console ready (users operator, viewer, norole have console roles)"
