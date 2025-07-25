import streamlit as st
import os  # Ensure os module is imported
import asyncio
import httpx
import hashlib
import hmac
from datetime import datetime, timedelta
import logging

# Hardcoded Facebook API Config
FACEBOOK_CLIENT_ID = "666532632765375"
FACEBOOK_CLIENT_SECRET = "b253efdfdf23f269a2807f2948cbfe3b"
FACEBOOK_AD_ACCOUNT_ID = "1332945887909560"
FACEBOOK_ACCESS_TOKEN = "EAAJeNTjOo78BPKWnC8jY4c4BzNaMiPKVcS4xBAlPXTJMhXxZCx61uWKTfCrqfHcnmB2w8ZBCfwtnJSvWuh3Q3K8ldI1IlzR4StFdD3gZCqbj1SHyZC0iBuofLrp0OjGsZAfb0eVsU0CgmUC3GG467ZC7JKVI2TpiU6opLZBO8TyhXSc8uwnxKf4qhUJSLu1WNLTBt5ED7BM"
FACEBOOK_API_VERSION = "v17.0"  # Default to v17.0 if not specified

# Set up logging
log_file = "streamlit_log.log"
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

def generate_appsecret_proof(access_token: str, app_secret: str) -> str:
    return hmac.new(
        app_secret.encode('utf-8'),
        access_token.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

# Async Functions
async def debug_token(access_token: str) -> dict:
    endpoint = "debug_token"
    params = {
        "input_token": access_token,
        "access_token": f"{FACEBOOK_CLIENT_ID}|{FACEBOOK_CLIENT_SECRET}"
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://graph.facebook.com/{FACEBOOK_API_VERSION}/{endpoint}",
                params=params
            )
            if response.status_code != 200:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
            return response.json()
    except Exception as e:
        return {"error": f"Exception: {str(e)}"}

async def exchange_short_lived_token(short_lived_token: str) -> dict:
    url = f"https://graph.facebook.com/{FACEBOOK_API_VERSION}/oauth/access_token"
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": FACEBOOK_CLIENT_ID,
        "client_secret": FACEBOOK_CLIENT_SECRET,
        "fb_exchange_token": short_lived_token
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            if response.status_code != 200:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
            data = response.json()
            expires_in = data.get("expires_in", 0)
            if expires_in > 0:
                expiration_date = datetime.now() + timedelta(seconds=expires_in)
                data["expires_at"] = expiration_date.isoformat()
            return data
    except Exception as e:
        return {"error": f"Exception: {str(e)}"}

async def refresh_token_if_needed(access_token: str, threshold_days: int = 7):
    token_info = await debug_token(access_token)
    if "error" in token_info:
        logging.warning(f"Meta token debug failed: {token_info['error']}")
        return access_token
    
    expires_at = token_info.get("data", {}).get("expires_at", 0)
    if expires_at:
        expiration_date = datetime.fromtimestamp(expires_at)
        days_left = (expiration_date - datetime.now()).days
        
        if days_left < threshold_days:
            logging.warning(f"Meta token expires in {days_left} days! Attempting automatic refresh...")
            refresh_result = await exchange_short_lived_token(access_token)
            if "error" not in refresh_result:
                new_token = refresh_result.get("access_token")
                if new_token:
                    expires_in = refresh_result.get("expires_in", 0)
                    logging.info(f":white_check_mark: Token refreshed successfully! New token expires in {expires_in} seconds")
                    return new_token
                else:
                    logging.error(":x: Token refresh failed: No access_token in response")
            else:
                logging.error(f":x: Token refresh failed: {refresh_result['error']}")
                logging.warning("Using original token - manual refresh may be required")
        else:
            logging.info(f"Meta token valid, expires in {days_left} days.")
    else:
        logging.info("Meta token is long-lived or does not expire.")
    
    return access_token

async def async_fetch_campaigns(start_date, end_date, access_token):
    url = f"https://graph.facebook.com/{FACEBOOK_API_VERSION}/act_{FACEBOOK_AD_ACCOUNT_ID}/insights"
    params = {
        "access_token": access_token,
        "fields": "campaign_id,campaign_name,impressions,clicks,spend,actions,date_start,date_stop",
        "time_range": {"since": str(start_date), "until": str(end_date)},
        "level": "campaign",
        "limit": 1000
    }
    
    all_data = []
    page_count = 0
    
    async with httpx.AsyncClient() as client:
        while True:
            page_count += 1
            logging.info(f"Fetching Meta Ads page {page_count}...")
            
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            response_data = resp.json()
            
            page_data = response_data.get("data", [])
            all_data.extend(page_data)
            
            logging.info(f"Page {page_count}: Got {len(page_data)} campaigns")
            
            paging = response_data.get("paging", {})
            next_url = paging.get("next")
            
            if not next_url:
                logging.info(f"No more pages. Total campaigns fetched: {len(all_data)}")
                break
            
            url = next_url
    
    result = []
    for row in all_data:
        result.append({
            "platform": "meta_ads",
            "campaign_id": row.get("campaign_id"),
            "campaign_name": row.get("campaign_name"),
            "impressions": int(row.get("impressions", 0)),
            "clicks": int(row.get("clicks", 0)),
            "cost": float(row.get("spend", 0)),
            "conversions": next((int(a["value"]) for a in row.get("actions", []) if a["action_type"] == "offsite_conversion"), 0),
            "date": row.get("date_start"),
        })
    
    return result

def fetch_meta_ads_data(start_date, end_date):
    access_token = FACEBOOK_ACCESS_TOKEN
    if not access_token:
        raise ValueError("FACEBOOK_ACCESS_TOKEN not found in environment variables")
    access_token = asyncio.run(refresh_token_if_needed(access_token))
    return asyncio.run(async_fetch_campaigns(start_date, end_date, access_token))


# Date range input
start_date = st.date_input("Start Date", datetime(2023, 1, 1))
end_date = st.date_input("End Date", datetime(2023, 12, 31))

# Button to fetch data
if st.button("Fetch Data"):
    try:
        campaign_data = fetch_meta_ads_data(start_date, end_date)
        if campaign_data:
            st.write("Campaign Data:")
            st.dataframe(campaign_data)
        else:
            st.warning("No data available for the selected date range.")
    except Exception as e:
        st.error(f"Error: {e}")

# Show logs (handle missing log file)
st.subheader("Logs")
if os.path.exists(log_file):
    with open(log_file, "r") as file:
        logs = file.readlines()
        for line in logs[-10:]:
            st.text(line)
else:
    st.warning("Log file not found. No logs to display.")
