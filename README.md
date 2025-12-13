# Self Hosted Cloudflared Tunnel Minecraft Servers

Host your minecraft servers through cloudflare tunnels.
Server management and dashboard is provided by this awesome project:
[https://github.com/nickheyer/discopanel](https://github.com/nickheyer/discopanel)

Key features:

- Continuous management of the **Cloudflared Tunnel** (create it, update config ingress rules for each server, etc.)
- Continuous management of the **DNS records** (for the dashboard + each server)
- **No port forwarding** (provide public addresses like **25565.example.com** for a server running on port **25565**)
- Servers run on an internal docker network.

## Prerequisites

- Cloudflare account
- Owned domain managed on Cloudflare

## Cloudflare API Token

Create an API token in your Cloudflare account with these permissions:

- Cloudflare One Connectors:Edit
- Cloudflare One Connector: cloudflared:Edit
- Cloudflare Tunnel:Edit
- DNS:Edit

## Setup Instructions

1. Clone the repository:

   ```sh
   git clone https://github.com/hunortakacs/cloudflared-minecraft.git
   cd cloudflared-minecraft
   ```

2. Create the main .env file with the mandatory fields:

   ```sh
   cp .env.example .env
   ```

3. Edit `.env` and fill in:
   - `CLOUDFLARE_API_TOKEN`
   - `ACCOUNT_ID`
   - `ZONE_ID`
   - `DOMAIN`
   - `DISCOPANEL_HOST_DATA_PATH`

4. Start the services:

   ```sh
   docker compose up -d
   ```

## Accessing the dashboard

- The web dashboard will be available at `<dashboard-subdomain>.<your-domain>`
- The default dashboard subdomain is `mc`, resulting in dashboard address like `mc.example.com`

## Accessing the servers

- Minecraft servers will be accessible at `<serverport>.<your-domain>` eg. `25565.example.com`
- The [Modflared](https://modrinth.com/mod/modflared) mod will be needed for connecting to servers

## Customization

You can configure some of the default options in `.env.defaults`, such as:

- `TUNNEL_NAME`
- `DASHBOARD_SUBDOMAIN`
- `MC_SERVER_RECORD_COMMENT`
- `MC_DASHBOARD_RECORD_COMMENT`
