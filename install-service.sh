#!/bin/bash

# Define colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if script is run as root
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Please run as root${NC}"
  exit 1
fi

SERVICE_NAME="lyrics-transliteration"
SERVICE_FILE="${SERVICE_NAME}.service"
DEST_PATH="/etc/systemd/system/${SERVICE_FILE}"

# Function to install the service
install_service() {
  echo "Installing ${SERVICE_NAME} service..."
  cp "${SERVICE_FILE}" "${DEST_PATH}"
  chmod 644 "${DEST_PATH}"
  systemctl daemon-reload
  echo -e "${GREEN}Service installed successfully${NC}"
}

# Check if service file exists
if [ ! -f "${SERVICE_FILE}" ]; then
  echo -e "${RED}Service file ${SERVICE_FILE} not found in current directory${NC}"
  exit 1
fi

# Install service if not already installed
if [ ! -f "${DEST_PATH}" ]; then
  install_service
else
  echo "Service already installed. Updating..."
  install_service
fi

case "$1" in
  start)
    echo "Starting service..."
    systemctl start "${SERVICE_NAME}"
    ;;
  stop)
    echo "Stopping service..."
    systemctl stop "${SERVICE_NAME}"
    ;;
  restart)
    echo "Restarting service..."
    systemctl restart "${SERVICE_NAME}"
    ;;
  status)
    echo "Service status:"
    systemctl status "${SERVICE_NAME}"
    ;;
  enable)
    echo "Enabling service to start on boot..."
    systemctl enable "${SERVICE_NAME}"
    echo -e "${GREEN}Service enabled${NC}"
    ;;
  disable)
    echo "Disabling service from starting on boot..."
    systemctl disable "${SERVICE_NAME}"
    echo -e "${GREEN}Service disabled${NC}"
    ;;
  uninstall)
    echo "Uninstalling service..."
    systemctl stop "${SERVICE_NAME}"
    systemctl disable "${SERVICE_NAME}"
    rm -f "${DEST_PATH}"
    systemctl daemon-reload
    echo -e "${GREEN}Service uninstalled${NC}"
    ;;
  *)
    echo "Usage: $0 {start|stop|restart|status|enable|disable|uninstall}"
    echo ""
    echo "Install the service and:"
    echo "  start      - Start the service"
    echo "  stop       - Stop the service"
    echo "  restart    - Restart the service"
    echo "  status     - Check service status"
    echo "  enable     - Enable service to start on boot"
    echo "  disable    - Disable service from starting on boot"
    echo "  uninstall  - Uninstall the service"
    exit 1
    ;;
esac

exit 0 