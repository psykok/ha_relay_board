# 8-Channel Relay Board — Home Assistant Integration

Custom component for controlling 8-channel relay boards that use the Keil EWEB firmware. Supports both TCP and REST (HTTP) protocols.

## Requirements

- Home Assistant 2024.1 or later
- An 8-channel relay board with Keil EWEB firmware, reachable on your network

## Installation

### Manual

1. Copy the `custom_components/relay_board_8` folder into your Home Assistant `config/custom_components/` directory:

   ```
   config/
   └── custom_components/
       └── relay_board_8/
           ├── __init__.py
           ├── button.py
           ├── config_flow.py
           ├── const.py
           ├── coordinator.py
           ├── manifest.json
           ├── strings.json
           ├── switch.py
           └── translations/
               └── en.json
   ```

2. Restart Home Assistant.

### HACS (manual repository)

1. In HACS, go to **Integrations** > three-dot menu > **Custom repositories**.
2. Add this repository URL and select category **Integration**.
3. Install **8-Channel Relay Board** from HACS.
4. Restart Home Assistant.

## Configuration

1. Go to **Settings > Devices & Services > Add Integration**.
2. Search for **8-Channel Relay Board**.
3. Enter:
   - **Host** — IP address of the relay board (e.g. `192.168.0.166`)
   - **Protocol** — choose TCP or REST (see below)
4. Depending on the protocol selected, a second step asks for protocol-specific settings.
5. Click **Submit**. The integration will test the connection before completing setup.

### Choosing a protocol

| | TCP | REST (HTTP) |
|---|---|---|
| **Port** | 1234 (default) | 80 (default) |
| **Authentication** | None | Basic auth (username/password) |
| **Reliability** | Recommended — lightweight, does not overload the board | May cause the board to become unavailable under load |
| **State updates** | Immediate on toggle + temporary polling (60s for 5 min) | Immediate on toggle, no polling |

**TCP (recommended)** — Uses raw TCP commands (`L{N}` on, `D{N}` off, `R{N}` state). Much lighter on the embedded server. No authentication required. After toggling a relay, the integration temporarily polls state every 60 seconds for 5 minutes to catch external changes, then stops.

**REST (HTTP)** — Uses HTTP POST to `/relay_en.cgi` with basic auth. State is parsed from the HTML response. No background polling. Suitable if TCP port 1234 is not available on your board.

### TCP setup

1. Select **TCP** as the protocol.
2. Enter the TCP port (default: `1234`).
3. The integration will send a test command to verify connectivity.

### REST setup

1. Select **REST (HTTP)** as the protocol.
2. Enter:
   - **HTTP Port** — default `80`
   - **Username** — default `admin`
   - **Password** — the device password
3. The integration will test HTTP connectivity and authentication.

## Usage

After setup, a single device named **Relay Board (your-ip)** appears with:

- **8 switch entities** (Relay 1 through Relay 8) — toggle individual relays
- **2 button entities** (All Relays On / All Relays Off) — control all relays at once

You can:

- Toggle relays from the device page or any dashboard
- Rename individual relays (e.g. "Garden Lights") via the entity settings
- Use switches in automations and scripts like any other HA switch
- Use the "All" buttons in automations via **Perform action** > `button.press`

## Troubleshooting

- **Cannot connect (TCP)** — Verify the board is reachable: `echo -e "R1\r\n" | nc <ip> 1234`. You should see `Relayon 1` or `Relayoff 1`.
- **Cannot connect (REST)** — Verify: `curl -X GET http://<ip>/relay_en.cgi --user admin:<password>`
- **Invalid auth** — Check username and password. The default username is usually `admin`.
- **Board becomes unavailable** — Switch to TCP protocol. REST/HTTP overloads the embedded web server over time.

## Removing

1. Go to **Settings > Devices & Services**.
2. Find the relay board entry and click **Delete**.
