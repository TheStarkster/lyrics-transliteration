# Lyrics Transliteration Service

A FastAPI service that separates vocals from music, transcribes lyrics, and generates English transliterations.

## Service Management

The application can be run as a systemd service for easier management.

### Installation and Setup

1. Make sure the service file and manager script are executable:
   ```
   chmod +x service_manager.sh
   ```

2. Install the service:
   ```
   sudo ./service_manager.sh install
   ```

3. Enable the service to start on boot:
   ```
   sudo ./service_manager.sh enable
   ```

### Service Commands

- **Start the service**:
  ```
  sudo ./service_manager.sh start
  ```

- **Stop the service**:
  ```
  sudo ./service_manager.sh stop
  ```

- **Restart the service**:
  ```
  sudo ./service_manager.sh restart
  ```

- **Check service status**:
  ```
  sudo ./service_manager.sh status
  ```

- **Disable service from starting on boot**:
  ```
  sudo ./service_manager.sh disable
  ```

## API Endpoints

- **Upload audio file**: `POST /upload/`
- **WebSocket connection**: `WebSocket /ws/{client_id}`
- **Set dummy mode**: `POST /set-dummy-mode/`

## Environment

The service uses the Python environment at `/home/azureuser/demucs-env` which should have all the required dependencies installed. 