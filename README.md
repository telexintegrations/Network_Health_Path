# Network Path Health API

## Overview
This API performs network diagnostics by checking for packet loss along the route to a target URL using `pathping` (Windows) or `mtr` (Linux/macOS). The results are then sent to a specified return URL for further processing.

## Features
- Runs network diagnostics in the background
- Supports both Windows (`pathping`) and Linux/macOS (`mtr`)
- Detects packet loss at different hops along the network route
- Sends results to a webhook (return URL)
- Uses FastAPI for API routing

## Installation

### Prerequisites
Ensure you have the following installed:
- Python 3.8+
- FastAPI
- httpx

### Steps
1. Clone the repository:
   ```sh
   git clone <repo-url>
   cd <repo-folder>
   ```
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Run the FastAPI server:
   ```sh
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

## API Endpoints

### 1. Check Network Health
**Endpoint:**
```
POST /network-health
```

**Payload:**
```json
{
  "channel_id": "12345",
  "return_url": "https://yourwebhook.com/receive",
  "settings": [
    { "label": "target_url", "type": "string", "required": true, "default": "www.example.com" }
  ]
}
```

**Response:**
```json
{
  "status": "accepted"
}
```

## How It Works
1. The API receives a request with a target URL.
2. It runs `pathping` (Windows) or `mtr` (Linux/macOS) to diagnose packet loss.
3. The function parses the output to detect packet loss per hop.
4. The results are sent to the provided `return_url` as a webhook.

## Example Output
- **No Packet Loss:**
  ```
  No packet loss detected to www.example.com.
  ```
- **With Packet Loss:**
  ```
  ⚠️ 20% packet loss detected at 192.168.1.1 while reaching www.example.com.
  ```

## Adding an Image
![WhatsApp Image 2025-02-22 at 22 14 58_327ce2b7](https://github.com/user-attachments/assets/e56fe7c2-7b4b-4a29-9de9-48d7d0c8babb)


## License
This project is licensed under the MIT License.

