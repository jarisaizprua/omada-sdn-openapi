import json
import os
from datetime import datetime

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TOKENS_FILE = "tokens.json"

BINDING_TYPE_MAP = {
    0: "No binding",
    1: "Static binding",
    2: "Dynamic binding",
}


def load_tokens(path=TOKENS_FILE):
    """Carga accessToken, omada_id e interface_access_address generados por omada_connect.py."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"No se encontró {path}. Ejecuta primero omada_connect.py")
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


def get_sites(base_url, omada_id, access_token, page=1, page_size=100):
    """Obtiene la lista de sites del controlador (GET /openapi/v1/{omadacId}/sites)."""
    url = f"{base_url}/openapi/v1/{omada_id}/sites"
    params = {"page": page, "pageSize": page_size}
    headers = {"Authorization": f"AccessToken={access_token}"}

    resp = requests.get(url, params=params, headers=headers, verify=False)
    resp.raise_for_status()
    data = resp.json()

    if data.get("errorCode") != 0:
        raise RuntimeError(f"Error obteniendo sites: {data}")

    return data["result"]["data"]


def get_local_users(base_url, omada_id, site_id, access_token, page=1, page_size=1000):
    """Obtiene la lista de usuarios locales de hotspot de un site
    (GET /openapi/v1/{omadacId}/sites/{siteId}/hotspot/localusers)."""
    url = f"{base_url}/openapi/v1/{omada_id}/sites/{site_id}/hotspot/localusers"
    params = {"page": page, "pageSize": page_size}
    headers = {"Authorization": f"AccessToken={access_token}"}

    resp = requests.get(url, params=params, headers=headers, verify=False)
    resp.raise_for_status()
    data = resp.json()

    error_code = data.get("errorCode")
    if error_code == -33000:
        raise RuntimeError(f"El site {site_id} no existe.")
    if error_code != 0:
        raise RuntimeError(f"Error obteniendo usuarios locales del site {site_id}: {data}")

    return data["result"]["data"], data["result"]["totalRows"]


def format_expiration(expiration_ms):
    """Convierte expirationTime (ms) a una fecha legible, o '-' si no aplica."""
    if not expiration_ms:
        return "-"
    try:
        return datetime.fromtimestamp(expiration_ms / 1000).strftime("%Y-%m-%d %H:%M")
    except (OSError, OverflowError, ValueError):
        return "-"


def print_local_users(site_name, users):
    """Imprime en consola los usuarios locales de un site (usuario, nombre, teléfono, estado, MAC, expiración)."""
    print(f"\nSite: {site_name}")

    if not users:
        print("    No hay usuarios locales configurados en este site.")
        return

    header = (
        f"{'Usuario':<18}{'Nombre':<16}{'Teléfono':<14}{'Habilitado':<12}"
        f"{'Binding':<16}{'MAC':<18}{'Expira':<18}"
    )
    print("    " + header)
    print("    " + "-" * len(header))

    for u in users:
        binding_text = BINDING_TYPE_MAP.get(u.get("bindingType"), f"Unknown({u.get('bindingType')})")
        mac = mask(u.get("macAddress", ""), visible=6) if u.get("macAddress") else "-"
        print(
            "    "
            f"{u.get('userName', ''):<18}"
            f"{u.get('name', ''):<16}"
            f"{u.get('phone', ''):<14}"
            f"{str(u.get('enable', '')):<12}"
            f"{binding_text:<16}"
            f"{mac:<18}"
            f"{format_expiration(u.get('expirationTime')):<18}"
        )


def main():
    tokens = load_tokens()
    base_url = tokens["interface_access_address"]
    omada_id = tokens["omada_id"]
    access_token = tokens["accessToken"]

    print(f"Usando accessToken: {mask(access_token)}")

    sites = get_sites(base_url, omada_id, access_token)

    if not sites:
        print("El controlador no tiene sites disponibles.")
        return

    for site in sites:
        users, total = get_local_users(base_url, omada_id, site["siteId"], access_token)
        print_local_users(f"{site['name']} ({site['siteId']}) - {total} usuario(s)", users)


if __name__ == "__main__":
    main()
