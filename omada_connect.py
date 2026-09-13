import json
import os
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

CREDENTIALS_FILE = "credentials.json"
TOKENS_FILE = "tokens.json"


def load_credentials(path=CREDENTIALS_FILE):
    """Carga client_id, client_secret, omadac_id, username, password y base_url desde un archivo JSON."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"No se encontró el archivo de credenciales: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def mask(value, visible=4):
    """Enmascara un valor sensible dejando visibles los últimos 'visible' caracteres (visible=0 oculta todo)."""
    if not value:
        return value
    value = str(value)
    if visible <= 0 or len(value) <= visible:
        return "*" * len(value)
    return "*" * (len(value) - visible) + value[-visible:]


def login(base_url, client_id, omada_id, username, password):
    """Autentica al usuario (POST /openapi/authorize/login) y devuelve csrfToken y sessionId."""
    url = f"{base_url}/openapi/authorize/login"
    params = {"client_id": client_id, "omadac_id": omada_id}
    body = {"username": username, "password": password}
    headers = {"content-type": "application/json"}

    print("[1] Login -> POST /openapi/authorize/login")
    print(f"    client_id: {mask(client_id)}")
    print(f"    omada_id : {mask(omada_id)}")
    print(f"    username : {mask(username, visible=3)}")
    print(f"    password : {mask(password, visible=0)}")

    resp = requests.post(url, params=params, json=body, headers=headers, verify=False)
    resp.raise_for_status()
    data = resp.json()

    if data.get("errorCode") != 0:
        raise RuntimeError(f"Error en login: {data}")

    csrf_token = data["result"]["csrfToken"]
    session_id = data["result"]["sessionId"]

    print(f"    csrfToken: {mask(csrf_token)}")
    print(f"    sessionId: {mask(session_id)}")
    print("    Login exitoso.\n")

    return csrf_token, session_id


def get_authorization_code(base_url, client_id, omada_id, csrf_token, session_id):
    """Obtiene el código de autorización (POST /openapi/authorize/code) usando csrfToken y sessionId."""
    url = f"{base_url}/openapi/authorize/code"
    params = {"client_id": client_id, "omadac_id": omada_id, "response_type": "code"}
    headers = {
        "content-type": "application/json",
        "Csrf-Token": csrf_token,
        "Cookie": f"TPOMADA_SESSIONID={session_id}",
    }

    print("[2] Obtener código de autorización -> POST /openapi/authorize/code")

    resp = requests.post(url, params=params, headers=headers, verify=False)
    resp.raise_for_status()
    data = resp.json()

    if data.get("errorCode") != 0:
        raise RuntimeError(f"Error obteniendo authorization code: {data}")

    auth_code = data["result"]

    print(f"    authorization_code: {mask(auth_code)}")
    print("    Código obtenido correctamente (válido 2 minutos).\n")

    return auth_code


def get_access_token(base_url, client_id, client_secret, auth_code):
    """Intercambia el código de autorización por el access token (POST /openapi/authorize/token)."""
    url = f"{base_url}/openapi/authorize/token"
    params = {"grant_type": "authorization_code", "code": auth_code}
    body = {"client_id": client_id, "client_secret": client_secret}
    headers = {"content-type": "application/json"}

    print("[3] Obtener access token -> POST /openapi/authorize/token")
    print(f"    client_secret: {mask(client_secret)}")

    resp = requests.post(url, params=params, json=body, headers=headers, verify=False)
    resp.raise_for_status()
    data = resp.json()

    if data.get("errorCode") != 0:
        raise RuntimeError(f"Error obteniendo access token: {data}")

    result = data["result"]

    print(f"    accessToken : {mask(result['accessToken'])}")
    print(f"    tokenType   : {result['tokenType']}")
    print(f"    expiresIn   : {result['expiresIn']} segundos")
    print(f"    refreshToken: {mask(result['refreshToken'])}")
    print("    Access token obtenido correctamente.\n")

    return result


def refresh_access_token(base_url, client_id, client_secret, refresh_token):
    """Renueva el access token usando el refresh token (POST /openapi/authorize/token, grant_type=refresh_token)."""
    url = f"{base_url}/openapi/authorize/token"
    params = {"client_id": client_id, "client_secret": client_secret,
              "refresh_token": refresh_token, "grant_type": "refresh_token"}
    headers = {"content-type": "application/json"}

    print("[4] Refrescar access token -> POST /openapi/authorize/token (refresh_token)")

    resp = requests.post(url, params=params, headers=headers, verify=False)
    resp.raise_for_status()
    data = resp.json()

    if data.get("errorCode") != 0:
        raise RuntimeError(f"Error refrescando access token: {data}")

    result = data["result"]

    print(f"    Nuevo accessToken : {mask(result['accessToken'])}")
    print(f"    Nuevo refreshToken: {mask(result['refreshToken'])}")
    print("    Access token refrescado correctamente.\n")

    return result


def save_tokens(tokens, omada_id, base_url, oauth_login_page_address, path=TOKENS_FILE):
    """Guarda accessToken, refreshToken y datos de conexión en un archivo JSON para uso posterior."""
    payload = {
        "interface_access_address": base_url,
        "oauth_login_page_address": oauth_login_page_address,
        "omada_id": omada_id,
        "accessToken": tokens["accessToken"],
        "refreshToken": tokens["refreshToken"],
        "tokenType": tokens["tokenType"],
        "expiresIn": tokens["expiresIn"],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"[5] Tokens guardados en {path} (para usarlos en el script de dispositivos).")


def main():
    creds = load_credentials()
    base_url = creds["interface_access_address"]

    csrf_token, session_id = login(
        base_url, creds["client_id"], creds["omada_id"],
        creds["username"], creds["password"]
    )

    auth_code = get_authorization_code(
        base_url, creds["client_id"], creds["omada_id"],
        csrf_token, session_id
    )

    tokens = get_access_token(
        base_url, creds["client_id"], creds["client_secret"], auth_code
    )

    save_tokens(tokens, creds["omada_id"], base_url, creds["oauth_login_page_address"])


if __name__ == "__main__":
    main()
