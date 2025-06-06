#!/bin/bash

SERVICE_NAME="lyrics_service"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Check if running with sudo
if [ "$EUID" -ne 0 ]; then
  echo "Please run with sudo: sudo $0 $1"
  exit 1
fi

# Function to install the service
install_service() {
  echo "Installing lyrics transliteration service..."
  cp ${SCRIPT_DIR}/lyrics_service.service ${SERVICE_FILE}
  systemctl daemon-reload
  echo "Service installed successfully."
}

# Main case statement for commands
case "$1" in
  install)
    install_service
    ;;
  start)
    echo "Starting lyrics transliteration service..."
    systemctl start ${SERVICE_NAME}
    ;;
  stop)
    echo "Stopping lyrics transliteration service..."
    systemctl stop ${SERVICE_NAME}
    ;;
  restart)
    echo "Restarting lyrics transliteration service..."
    systemctl restart ${SERVICE_NAME}
    ;;
  status)
    echo "Checking status of lyrics transliteration service..."
    systemctl status ${SERVICE_NAME}
    ;;
  enable)
    echo "Enabling service to start on boot..."
    systemctl enable ${SERVICE_NAME}
    ;;
  disable)
    echo "Disabling service from starting on boot..."
    systemctl disable ${SERVICE_NAME}
    ;;
  *)
    echo "Usage: sudo $0 {install|start|stop|restart|status|enable|disable}"
    exit 1
    ;;
esac

exit 0 