import json
import os
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TOKENS_FILE = "tokens.json"

STATUS_MAP = {
    0: "Disconnected",
    1: "Connected",
    2: "Pending",
    3: "Heartbeat Missed",
    4: "Isolated",
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


def get_devices(base_url, omada_id, site_id, access_token, page=1, page_size=1000):
    """Obtiene la lista de dispositivos de un site (GET /openapi/v1/{omadacId}/sites/{siteId}/devices)."""
    url = f"{base_url}/openapi/v1/{omada_id}/sites/{site_id}/devices"
    params = {"page": page, "pageSize": page_size}
    headers = {"Authorization": f"AccessToken={access_token}"}

    resp = requests.get(url, params=params, headers=headers, verify=False)
    resp.raise_for_status()
    data = resp.json()

    if data.get("errorCode") != 0:
        raise RuntimeError(f"Error obteniendo dispositivos: {data}")

    return data["result"]["data"], data["result"]["totalRows"]


def print_devices(site_name, devices):
    """Imprime en consola los datos relevantes de los dispositivos de un site (modelo, firmware, estado, etc.)."""
    print(f"\nSite: {site_name}")

    if not devices:
        print("    No se encontraron dispositivos en este site.")
        return

    header = (
        f"{'Nombre':<20}{'Modelo':<16}{'Firmware':<30}{'IP':<16}{'Estado':<18}{'MAC':<18}"
    )
    print("    " + header)
    print("    " + "-" * len(header))

    for d in devices:
        status_text = STATUS_MAP.get(d.get("status"), f"Unknown({d.get('status')})")
        print(
            "    "
            f"{d.get('name', ''):<20}"
            f"{d.get('modelName', ''):<16}"
            f"{d.get('firmwareVersion', ''):<30}"
            f"{d.get('ip', ''):<16}"
            f"{status_text:<18}"
            f"{mask(d.get('mac', ''), visible=6):<18}"
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
        devices, total = get_devices(base_url, omada_id, site["siteId"], access_token)
        print_devices(f"{site['name']} ({site['siteId']}) - {total} dispositivo(s)", devices)


if __name__ == "__main__":
    main()
