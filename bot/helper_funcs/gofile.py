import aiohttp
import os
import logging

LOGGER = logging.getLogger(__name__)

async def get_server():
    """Get the available gofile server for upload."""
    url = "https://api.gofile.io/servers"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status") == "ok":
                        servers = data.get("data", {}).get("servers", [])
                        if servers:
                            # Picking the first server is generally fine as it's the recommended one
                            return servers[0].get("name")
    except Exception as e:
        LOGGER.error(f"Error getting gofile server: {e}")
    return None

async def upload_gofile(file_path, token=None):
    """Upload a file to gofile.io."""
    server = await get_server()
    if not server:
        LOGGER.error("Could not get gofile server.")
        return None

    url = f"https://{server}.gofile.io/contents/uploadfile"
    file_name = os.path.basename(file_path)

    try:
        # We use a context manager for the file to ensure it's closed correctly
        with open(file_path, 'rb') as f:
            data = aiohttp.FormData()
            # Adding filename explicitly improves reliability
            data.add_field('file', f, filename=file_name)
            if token:
                data.add_field('token', token)

            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("status") == "ok":
                            return result.get("data", {}).get("downloadPage")
                        else:
                            LOGGER.error(f"Gofile upload error for {file_name}: {result}")
                    else:
                        text = await response.text()
                        LOGGER.error(f"Gofile upload failed for {file_name} with status {response.status}: {text}")
    except Exception as e:
        LOGGER.error(f"Error in gofile upload for {file_name}: {e}")
    return None
