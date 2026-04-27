# 8-Channel Relay Board — Home Assistant Integration

Custom component for controlling 8-channel relay boards that use the Keil EWEB web interface.

## Requirements

- Home Assistant 2024.1 or later
- An 8-channel relay board with Keil EWEB firmware, reachable on your network via HTTP

## Installation

### Manual

1. Copy the `custom_components/relay_board_8` folder into your Home Assistant `config/custom_components/` directory:

   ```
   config/
   └── custom_components/
       └── relay_board_8/
           ├── __init__.py
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
   - **Port** — HTTP port (default: `80`)
   - **Username** — admin username (default: `admin`)
   - **Password** — device password
4. Click **Submit**. The integration will test the connection before completing setup.

## Usage

After setup, a single device named **Relay Board (your-ip)** appears with 8 switch entities (Relay 1 through Relay 8). You can:

- Toggle relays from the device page or any dashboard
- Rename individual relays (e.g. "Garden Lights") via the entity settings
- Use them in automations and scripts like any other HA switch

## Troubleshooting

- **Cannot connect** — Verify the board is reachable: `curl -X GET http://<ip>/relay_en.cgi --user admin:<password>`
- **Invalid auth** — Check username and password. The default username is usually `admin`.
- **Switches not updating** — The integration polls the board every 30 seconds. State also updates immediately after toggling.

## Removing

1. Go to **Settings > Devices & Services**.
2. Find the relay board entry and click **Delete**.
