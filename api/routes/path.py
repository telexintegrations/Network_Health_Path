import platform
import subprocess
import re
from fastapi import APIRouter, status, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
import httpx
import logging
import time

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
    """Parses the network diagnostic output to detect packet loss at each hop, handling missing RTT values."""
    packet_loss_report = []

    hop_regex = re.compile(
        r"^\s*(\d+)\s+([\d\.\-*]+)\s+(\d+ms|\*|-{3})"
    )

    for line in output.split("\n"):
        match = hop_regex.search(line)
        if match:
            hop_number = match.group(1)
            ip_address = match.group(2)
            rtt = match.group(3)

            # Skip hops where RTT is missing or displayed as "---"
            if rtt in ["*", "---"]:
                continue

            # Detect packet loss
            loss_match = re.search(r"(\d+)/\s*\d+\s*=\s*(\d+)%", line)
            if loss_match:
                loss_percent = int(loss_match.group(2))
                if loss_percent > 0:
                    packet_loss_report.append(
                        f"⚠️ {loss_percent}% packet loss detected at {ip_address} (Hop {hop_number}) while reaching {target_url}."
                    )

    return "\n".join(packet_loss_report) if packet_loss_report else f"No packet loss detected to {target_url}."


def run_network_diagnostics(target: str) -> str:
    """Runs `pathping` (Windows) or `mtr` (Linux/macOS) to check packet loss."""
    system = platform.system()

    if system == "Windows":
        command = ["pathping", "-q", "5", "-p", "100", target]
    else:
        command = ["mtr", "-rw", "-c", "60", target]

    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        output, error = process.communicate()  # Waits until process completes

        logger.info("Raw Network Diagnostic Output:\n%s", output)

        if process.returncode == 0:
            return parse_packet_loss(output, target)
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
    output = run_network_diagnostics(target_url)

    async with httpx.AsyncClient() as client:
        data = {
            "message": output,
            "username": "Network Path Health",
            "event_name": "Network Diagnostics",
            "status": "success" if "❌" not in output else "error"
        }

        logger.info(f"Sending data to Telex channel: {data}")
        try:
            response = await client.post(payload.return_url, json=data)
            logger.info(f"📡 Response: {response.status_code}")
        except httpx.RequestError as e:
            logger.error(f"❌ Failed to send data to {payload.return_url}: {e}")

@router.post("/network-health")
async def check_health(payload: MonitorPayload, background_tasks: BackgroundTasks):
    """API endpoint to start network diagnostics in the background."""
    background_tasks.add_task(check_network_health, payload)
    return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content={"status": "accepted"})
