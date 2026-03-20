/* WebAuthn browser API helpers for registration and authentication. */

function bufferToBase64url(buffer) {
  const bytes = new Uint8Array(buffer);
  let str = '';
  for (const b of bytes) str += String.fromCharCode(b);
  return btoa(str).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

function base64urlToBuffer(base64url) {
  const base64 = base64url.replace(/-/g, '+').replace(/_/g, '/');
  const padded = base64 + '='.repeat((4 - base64.length % 4) % 4);
  const binary = atob(padded);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return bytes.buffer;
}

function setStatus(msg, isError) {
  const el = document.getElementById('auth-status');
  if (el) {
    el.textContent = msg;
    el.className = 'auth-status' + (isError ? ' auth-status-error' : '');
  }
}

async function startRegistration(optionsUrl, verifyUrl) {
  setStatus('Starting registration…', false);
  try {
    const optResp = await fetch(optionsUrl, { method: 'POST' });
    if (!optResp.ok) throw new Error('Failed to get registration options');
    const options = await optResp.json();

    // Decode challenge and user.id from base64url
    options.challenge = base64urlToBuffer(options.challenge);
    options.user.id = base64urlToBuffer(options.user.id);
    if (options.excludeCredentials) {
      options.excludeCredentials = options.excludeCredentials.map(c => ({
        ...c, id: base64urlToBuffer(c.id)
      }));
    }

    const credential = await navigator.credentials.create({ publicKey: options });

    const body = {
      id: credential.id,
      rawId: bufferToBase64url(credential.rawId),
      type: credential.type,
      response: {
        attestationObject: bufferToBase64url(credential.response.attestationObject),
        clientDataJSON: bufferToBase64url(credential.response.clientDataJSON),
      },
    };

    const verifyResp = await fetch(verifyUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    if (!verifyResp.ok) throw new Error('Registration verification failed');
    setStatus('Registration successful! Redirecting…', false);
    window.location.href = '/inbox';
  } catch (err) {
    setStatus('Registration failed: ' + err.message, true);
  }
}

async function startAuthentication(optionsUrl, verifyUrl) {
  setStatus('Starting authentication…', false);
  try {
    const optResp = await fetch(optionsUrl, { method: 'POST' });
    if (!optResp.ok) throw new Error('Failed to get authentication options');
    const options = await optResp.json();

    options.challenge = base64urlToBuffer(options.challenge);
    if (options.allowCredentials) {
      options.allowCredentials = options.allowCredentials.map(c => ({
        ...c, id: base64urlToBuffer(c.id)
      }));
    }

    const assertion = await navigator.credentials.get({ publicKey: options });

    const body = {
      id: assertion.id,
      rawId: bufferToBase64url(assertion.rawId),
      type: assertion.type,
      response: {
        authenticatorData: bufferToBase64url(assertion.response.authenticatorData),
        clientDataJSON: bufferToBase64url(assertion.response.clientDataJSON),
        signature: bufferToBase64url(assertion.response.signature),
        userHandle: assertion.response.userHandle
          ? bufferToBase64url(assertion.response.userHandle)
          : null,
      },
    };

    const verifyResp = await fetch(verifyUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    if (!verifyResp.ok) throw new Error('Authentication verification failed');
    setStatus('Authenticated! Redirecting…', false);
    window.location.href = '/inbox';
  } catch (err) {
    setStatus('Authentication failed: ' + err.message, true);
  }
}
