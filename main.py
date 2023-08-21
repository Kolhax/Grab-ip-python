from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
import hashlib
from datetime import datetime
import requests
from fastapi.templating import Jinja2Templates
import json
from discord import Embed

app = FastAPI()

# Templates
templates = Jinja2Templates(directory="templates")

# Load the existing data from the JSON file
try:
    with open("shortened_links.json", "r") as f:
        db = json.load(f)
except FileNotFoundError:
    db = {}

# Request model for creating short links
class ShortenLinkRequest(BaseModel):
    url: str
    webhook: str

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("shorten.html", {"request": request})

@app.post("/shorten")
def shorten_link(request: ShortenLinkRequest):
    # Generate a unique hash for the URL
    hash_object = hashlib.md5(request.url.encode())
    short_link = hash_object.hexdigest()[:6]
    
    # Store the short link, URL, and webhook in the database
    db[short_link] = {"url": request.url, "webhook": request.webhook}
    
    # Update the JSON file with the new data
    with open("shortened_links.json", "w") as f:
        json.dump(db, f, indent=4)
    
    return {"short_link": short_link}

@app.get("/s/{short_link}")
def redirect_to_original_url(short_link: str, request: Request):
    if short_link not in db:
        raise HTTPException(status_code=404, detail="Short link not found")
    
    original_url = db[short_link]["url"]
    webhook_url = db[short_link]["webhook"]
    
    # Extract the user's IP address from the request
    user_ip = request.client.host
    
    # Create an embed
    embed = Embed(
        title=f"Shortened URL '{short_link}' visited",
        description=f"Visited by IP: {user_ip}",
        color=0x3498db  # Use the color code you prefer
    )
    embed.set_footer(text=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    # Send the embed to the webhook using requests
    payload = {
        "embeds": [embed.to_dict()]
    }
    headers = {
        "Content-Type": "application/json"
    }
    requests.post(webhook_url, json=payload, headers=headers)
    
    # Redirect to the original URL
    return RedirectResponse(url=original_url)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
