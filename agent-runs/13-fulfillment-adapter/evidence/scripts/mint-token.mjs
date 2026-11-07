// Mints a local test JWT shaped like a Keycloak box1-realm token. Usage: node mint-token.mjs <private-key.pem> [role|-] [audience]
// The key is a throwaway generated per run in a scratch directory; this script never sees a real credential.
import { createSign } from 'node:crypto';
import { readFileSync } from 'node:fs';
const [key, role = 'fulfillment-writer', aud = 'fulfillment-adapter'] = process.argv.slice(2);
const b64 = o => Buffer.from(JSON.stringify(o)).toString('base64url');
const now = Math.floor(Date.now() / 1000);
const claims = { iss: 'run13-local', aud, sub: 'run13-operator', preferred_username: 'run13-operator', iat: now, exp: now + 3600,
  resource_access: role === '-' ? {} : { 'fulfillment-adapter': { roles: [role] } } };
const unsigned = `${b64({ alg: 'RS256', typ: 'JWT' })}.${b64(claims)}`;
const sig = createSign('RSA-SHA256').update(unsigned).sign(readFileSync(key)).toString('base64url');
console.log(`${unsigned}.${sig}`);
