import platform
import subprocess
import re
from fastapi import APIRouter, status, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
import httpx
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Setting(BaseModel):
    label: str
    type: str
    required: bool
    default: str

class MonitorPayload(BaseModel):
    channel_id: str
    return_url: str
    settings: List[Setting]

router = APIRouter()

def parse_packet_loss(output: str, target_url: str) -> str:
    """Parses the network diagnostic output to detect packet loss at each hop."""
    packet_loss_report = []
    
    # Windows `pathping` output pattern (Example: "  2   192.168.1.1      5/ 100 =  5%  |")
    pathping_regex = re.compile(r"(\d+)/\s*\d+\s*=\s*(\d+)%.*?(\d+\.\d+\.\d+\.\d+)")

    # Linux/macOS `mtr` output pattern (Example: "192.168.1.1        5.0%   |")
    mtr_regex = re.compile(r"(\d+\.\d+\.\d+\.\d+)\s+(\d+)%")

    for line in output.split("\n"):
        match = pathping_regex.search(line) or mtr_regex.search(line)
        if match:
            loss_percent = int(match.group(2))  # Packet loss percentage
            ip_address = match.group(3) if pathping_regex.search(line) else match.group(1)  # IP Address

            if loss_percent > 0:
                if ip_address:
                    packet_loss_report.append(f"⚠️ {loss_percent}% packet loss detected at {ip_address} while reaching {target_url}.")
                else:
                    packet_loss_report.append(f"⚠️ {loss_percent}% packet loss detected at an unknown hop while reaching {target_url}.")

    return "\n".join(packet_loss_report) if packet_loss_report else f"No packet loss detected to {target_url}."

def run_network_diagnostics(target: str) -> str:
    """Runs `pathping` (Windows) or `mtr` (Linux/macOS) to check packet loss."""
    system = platform.system()

    if system == "Windows":
        command = ["pathping", "-q", "5", "-p", "100", target]  # Windows command
    else:
        command = ["mtr", "-r", "-c", "5", target]  # Linux/macOS command

    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        output, error = process.communicate()  # No timeout, let it run as long as needed

        logger.info("Raw Network Diagnostic Output:\n%s", output)

        if process.returncode == 0:
            return parse_packet_loss(output, target)  # Pass target_url for formatting
        else:
            return f"❌ Error running network diagnostics: {error}"
    except Exception as e:
        return f"❌ An unexpected error occurred: {e}"

async def check_network_health(payload: MonitorPayload):
    """Runs network diagnostics and sends results to `return_url`."""
    settings_dict = {setting.label.lower(): setting.default for setting in payload.settings}
    target_url = settings_dict.get("target_url")

    if not target_url:
        logger.error("❌ Error: No target URL provided.")
        return

    logger.info(f"🔍 Running network diagnostics on {target_url}...")
    output = run_network_diagnostics(target_url)  # Call the function here

    packet_loss_detected = "⚠️" in output 

    async with httpx.AsyncClient() as client:
        data = {
            "message": output,
            "username": "Network Path Health",
            "event_name": "Network Diagnostics",
            "status": "success"
        }

        logger.info(f"Sending data to Telex channel: {data}")
        try:
            response = await client.post(payload.return_url, json=data)
            logger.info(f"📡 Response: {response.status_code}")
            logger.info(f"Data: {data}")
            logger.info(response.json())
        except httpx.RequestError as e:
            logger.error(f"❌ Failed to send data to {payload.return_url}: {e}")

@router.post("/network-health")
async def check_health(payload: MonitorPayload, background_tasks: BackgroundTasks):
    """API endpoint to start network diagnostics in the background."""
    background_tasks.add_task(check_network_health, payload)
    return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content={"status": "accepted"})