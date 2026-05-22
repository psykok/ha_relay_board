"""Constants for the 8-Channel Relay Board integration."""

import logging

DOMAIN = "relay_board_8"
LOGGER = logging.getLogger(__package__)

NUM_RELAYS = 8

CONF_PROTOCOL = "protocol"
PROTOCOL_REST = "rest"
PROTOCOL_TCP = "tcp"

DEFAULT_REST_PORT = 80
DEFAULT_TCP_PORT = 1234
