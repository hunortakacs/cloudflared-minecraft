#!/usr/bin/env python3
import os
import logging
import logs
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import api as cf
import subprocess
import requests

REQUIRED_VARS = [
    "DISCOPANEL_HOST_DATA_PATH",
    "DOMAIN",
    "DASHBOARD_SUBDOMAIN",
    "TUNNEL_NAME",
    "MC_SERVER_RECORD_COMMENT",
    "MC_DASHBOARD_RECORD_COMMENT",
]

for var in REQUIRED_VARS:
    if not os.environ.get(var):
        raise EnvironmentError(f"Error: {var} not set")

DOMAIN = os.environ["DOMAIN"]
DASHBOARD_SUBDOMAIN = os.environ["DASHBOARD_SUBDOMAIN"]
TUNNEL_NAME = os.environ["TUNNEL_NAME"]
MC_SERVER_RECORD_COMMENT = os.environ["MC_SERVER_RECORD_COMMENT"]
MC_DASHBOARD_RECORD_COMMENT = os.environ["MC_DASHBOARD_RECORD_COMMENT"]
HOST_PATH = Path(os.environ["DISCOPANEL_HOST_DATA_PATH"])
SERVERS_PATH = HOST_PATH / "servers"
DB_PATH = HOST_PATH / "discopanel.db"


logs.setup_format()
server_port_map = {}
tunnel_id = None


def fetch_servers():
    logging.info("Fetching server list from DiscoPanel API...")
    resp = requests.get("http://discopanel:8080/api/v1/servers")
    servers = resp.json()
    return {str(s["id"]): str(s["port"]) for s in servers}


def get_container_name(server_id: str) -> str:
    return f"discopanel-server-{server_id}"


def update_dns_and_tunnel_config():
    global server_port_map, tunnel_id
    server_port_map = fetch_servers()

    logging.info("Updating DNS records and tunnel config...")
    records = cf.list_records(
        params={"name.endswith": f".{DOMAIN}", "comment": MC_SERVER_RECORD_COMMENT})
    record_map = {}

    for r in records:
        port = r["name"].removesuffix(f".{DOMAIN}")
        if port not in server_port_map.values():
            cf.delete_record(r["id"])
        else:
            entry = record_map.get(port, {})
            entry[r["type"]] = r
            record_map[port] = entry

    ingress = [{"hostname": f"{DASHBOARD_SUBDOMAIN}.{DOMAIN}",
                "service": "http://discopanel:8080"}]

    for server_id, port in server_port_map.items():
        name = f"{port}.{DOMAIN}"

        cname = record_map.get(port, {}).get("CNAME")
        txt = record_map.get(port, {}).get("TXT")

        if not cname:
            cf.create_record(
                "CNAME", name, f"{tunnel_id}.cfargotunnel.com", comment=MC_SERVER_RECORD_COMMENT)
        elif cname["content"] != f"{tunnel_id}.cfargotunnel.com":
            cf.update_record(
                cname["id"], "CNAME", name, f"{tunnel_id}.cfargotunnel.com")
        if not txt:
            cf.create_record(
                "TXT", name, '"cloudflared-use-tunnel"', proxied=False, comment=MC_SERVER_RECORD_COMMENT)
        elif txt["content"] != '"cloudflared-use-tunnel"':
            cf.update_record(
                txt["id"], "TXT", name, '"cloudflared-use-tunnel"')

        service = f"tcp://{get_container_name(server_id)}:{port}"
        ingress.append({"hostname": name, "service": service})

    ingress.append({"service": "http_status:404"})
    cf.update_tunnel_config(tunnel_id, ingress)


class ServersFolderHandler(FileSystemEventHandler):
    def _folder_changed(self, event):
        global server_port_map
        if event.is_directory and Path(event.src_path).parent == SERVERS_PATH:
            logging.info(
                f"Server directory {event.event_type} at: {event.src_path}")
            update_dns_and_tunnel_config()

    def on_created(self, event):
        self._folder_changed(event)

    def on_deleted(self, event):
        self._folder_changed(event)


if __name__ == "__main__":
    tunnel_id, tunnel_token = cf.get_or_create_tunnel(TUNNEL_NAME)

    cf.set_record(
        "CNAME", f"{DASHBOARD_SUBDOMAIN}.{DOMAIN}", f"{tunnel_id}.cfargotunnel.com", comment=MC_DASHBOARD_RECORD_COMMENT)

    update_dns_and_tunnel_config()

    observer = Observer()
    observer.schedule(ServersFolderHandler(), str(HOST_PATH), recursive=True)
    observer.start()

    subprocess.run([
        "cloudflared", "tunnel", "run", "--token", tunnel_token
    ])

    observer.stop()
    observer.join()
