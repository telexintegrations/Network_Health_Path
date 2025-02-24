from fastapi import APIRouter, status, Request
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/integration.json")
async def integration(request: Request):
    # base_url = str(request.base_url).rstrip("/")
    base_url = "tqvjrlgn-8000.uks1.devtunnels.ms"
    # telex_channel_webhook = "https://ping.telex.im/v1/webhooks/019519ce-8dd0-77d8-a5b4-20227ee0b485"
    return{
        "data" : {
            "date": {
            "created_at": "2025-02-22",
            "updated_at": "2025-02-22"
            },
            "descriptions": {
                "app_name": "Network Health Path",
                "app_description": "Troubleshooting network outage to get the exact path causing packet loss and report to the telex channel.",
                "app_logo": "https://asset.cloudinary.com/dcoalw1ak/59753e5fc8b83bf1380e8297e89f7b2e",
                "app_url": f"{base_url}",
                "background_color": "#fff"
            },
            "is_active": True,
            "integration_type": "interval",
            "key_features": [
                "Troubleshoots network outage to get exact path causing packet loss"
            ],
            "integration_category": "Monitoring & Logging",
            "author": "Blessing Etuk",
            "website": f"{base_url}",
            "settings": [
                {
                    "label": "target_URL",
                    "type": "text",
                    "required": True,
                    "default": "google.com"
                },
                {
                    "label": "interval",
                    "type": "text",
                    "required": True,
                    "default": "* * * * *"
                }
            ],
            "tick_url": f"{base_url}/network-health",
            "target_url": f"{base_url}/network-health",
        }
    }
    

