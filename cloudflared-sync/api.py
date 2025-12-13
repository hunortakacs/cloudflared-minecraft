import os
import requests
import logging

CF_API = "https://api.cloudflare.com/client/v4"

REQUIRED_VARS = [
    "CLOUDFLARE_API_TOKEN",
    "ACCOUNT_ID",
    "ZONE_ID",
]

for var in REQUIRED_VARS:
    if not os.environ.get(var):
        raise EnvironmentError(f"Error: {var} not set")

API_TOKEN = os.environ["CLOUDFLARE_API_TOKEN"]
ACCOUNT_ID = os.environ["ACCOUNT_ID"]
ZONE_ID = os.environ["ZONE_ID"]


def cf_request(method, url, **kwargs):
    headers = kwargs.pop("headers", {})
    headers.update({"Authorization": f"Bearer {API_TOKEN}"})
    response = requests.request(method, url, headers=headers, **kwargs)
    response.raise_for_status()
    return response.json()


def get_or_create_tunnel(tunnel_name):
    logging.info("Estabilishing Cloudflared Tunnel...")
    resp = cf_request("GET", f"{CF_API}/accounts/{ACCOUNT_ID}/cfd_tunnel",
                      params={"is_deleted": "false", "name": tunnel_name})
    tunnels = resp.get("result", [])
    tunnel = next((t for t in tunnels if t["name"] == tunnel_name), None)

    if not tunnel:
        logging.info("No existing tunnel found, creating a new one...")
        resp = cf_request("POST", f"{CF_API}/accounts/{ACCOUNT_ID}/cfd_tunnel",
                          json={"name": tunnel_name, "config_src": "cloudflare"})
        tunnel = resp.get("result")

    tunnel_id = tunnel.get("id")
    resp = cf_request(
        "GET", f"{CF_API}/accounts/{ACCOUNT_ID}/cfd_tunnel/{tunnel_id}/token")
    tunnel_token = resp.get("result")

    if not tunnel_id:
        raise RuntimeError("Failed to obtain tunnel ID")
    if not tunnel_token:
        raise RuntimeError("Failed to obtain tunnel token")

    return tunnel_id, tunnel_token


def list_records(params={}):
    resp = cf_request(
        "GET", f"{CF_API}/zones/{ZONE_ID}/dns_records", params=params)
    result = resp.get("result", [])
    return [{
        "id": r["id"],
        "type": r["type"],
        "name": r["name"],
        "content": r["content"]
    } for r in result]


def create_record(record_type, name, content, proxied=True, comment=""):
    logging.info(f"Creating {record_type} record for {name}")
    data = {"type": record_type, "name": name, "content": content,
            "ttl": 1, "proxied": proxied, "comment": comment}
    resp = cf_request(
        "POST", f"{CF_API}/zones/{ZONE_ID}/dns_records", json=data)
    return resp.get("success", False)


def update_record(record_id, record_type, name, content, comment=""):
    logging.info(f"Updating {record_type} record for {name}")
    data = {"type": record_type, "name": name,
            "content": content, "comment": comment}
    resp = cf_request(
        "PATCH", f"{CF_API}/zones/{ZONE_ID}/dns_records/{record_id}", json=data)
    return resp.get("success", False)


def delete_record(record_id):
    logging.info(f"Deleting record {record_id}")
    resp = cf_request(
        "DELETE", f"{CF_API}/zones/{ZONE_ID}/dns_records/{record_id}")
    return resp.get("success", False)


def set_record(record_type, name, content, comment):
    records = list_records(
        params={"name.exact": name, "type": record_type})
    record = records[0] if records else None

    if record:
        return update_record(record["id"], record_type, name, content, comment=comment)
    else:
        return create_record(record_type, name, content, comment=comment)


def update_tunnel_config(tunnel_id, ingress):
    cf_request(
        "PUT",
        f"{CF_API}/accounts/{ACCOUNT_ID}/cfd_tunnel/{tunnel_id}/configurations",
        json={"config": {"ingress": ingress}}
    )
