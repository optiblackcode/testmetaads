import streamlit as st
import json
import tempfile
import os
from datetime import datetime, timedelta, date
from google.ads.googleads.client import GoogleAdsClient
from google.oauth2 import service_account
import pandas as pd
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Hardcoded service account credentials
SERVICE_ACCOUNT_JSON = {
    "type": "service_account",
    "project_id": "mxproxytracking",
    "private_key_id": "1b0f5e3366972916314122963c203bc3f443f4b9",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQChhb7mYt/d9coK\nP8pmLmR+vvRzudeTMhzBNseOozAq2Bt5OOhJVJ7OR+4jMSPoicdBj1Jar9IIH7bO\nkRB3luSbqtXmSOEUk3HVpGjFs9R4e1XKxGYJJnVdH0KP80HICQCIT3VdKu95/J3b\no0j3rr7w+fDaTawuyFCSDeYUdIAVhpCUaDuS4atf6UjpiRlnEo/LHbxRGV1zvwFS\nunE/5dcBstErCNjrmh/b5B8HyegiaETWS52TV+Sfj2qmWKMyqKukgt44N+hyqaEG\noHebI6IEQyeU+xtoLqtMuZMuUkuhCzs8c/S9uDrbj9fSEc5xGjfiHFMy889Xuu2W\nUxLUghdJAgMBAAECggEABZBJ5NLTjhLyYxDS8TBDEb2Umywz1tQN+wF0IBToFWsN\nDot4BCydbWgQtcFye0b2/X+zu8AczompyOrkw7scw+2UwWz8ZHJ2uZVDREoUimjf\nKeVCyX5mYlnaYlh5SSwMNWXH77iz99eh0rKzZ6VV2jmVwwM+vXwfZa8uYBZ/jJ41\nrA+zUwp761yiQr8Bb7BxYaC1AychrYJlyEU7GzNTuFoS+Y1YaAwmu9S6Z8cMQWED\nCO0mMwZLJH+nrB1jED0oQur5pLVM+rCZTAACNw/fHQ2heafHO96lE2bjYtvgFyTF\nxpXxTy0uqTwCp00/VWS6MXSczvBLPQhZ+RK1PFg1YQKBgQDc2xup/uJZoSQQ7J+j\ns6db0JtvQOyA2MrBTLy3YfUSJjvOnqWRONtxIlaYQP26eJ6mpuqx9PXfazciAidb\nXYzS41F5xa9kTuYYgVHu136g5RxmCNxmsNKcq4PrY7urWvdrFHg/m0R7c7ucajEg\niUhYtCdhz2mMk2VvtoeMSMgdGQKBgQC7OZoOMO6uiVxL84HMHIn+YLHgg4ANpV6I\ngd1TTQSOuXK4YwQI7oyoi9r5Nb/vu+u5dzo8Qe5d/EyLw8wQ9YIBNmNUln0ZCklL\nddvPqXxUQ8gR6KqospKVEJhjXw1Amxus7CqOKEixBa1nZkNwVu4NY8n9VnMAmx7N\nUBKh9IvhsQKBgAkU/Ys9DwPOi5QiluH9dklhR7MIgXE++P9/71a/MXvAlL8HaRmS\ns/twBQ2XxpdPdH636HjO8PlyCD9exU2NiEf3zxbp2S+PywiA8OSYef2VzlgnzyBt\n7wtARll8rW/7eqctnVBIS0WkWbex6jlDS/VR2zi7dcSxHv+8CtDrAUepAoGANbRl\nM3Ln1FsEhajY76K0FqrH+13dKozoHAIcaZurFgGuHaQRcTp0UJilfFzlrK/cAzxn\nEQfch0sq7eCBNdAmtZBTV90/DyK7OZEaN2wnhMhYqIJ0CaYHlAjJnZ+TXpffjW/F\nGTgG+fhl8EYOTDgzWtXoB+p3XJIieMRiQ+CxC1ECgYEAuhSHiTpkCZV7pVLdlNva\nNq04ZHshR3Y+jBjDHaSln7RSx13mm8iNz1zf3z/HehlJCnPrgoFBdhOnbowmWpm1\nSljzd5fVk/bhZdw8H+uPelE/77dgxZ6Z91lniQqDb2r57wAir+3fx66dzy2sVAXf\nTCn/YYyDtT1+7bqW/bqelQ4=\n-----END PRIVATE KEY-----\n",
    "client_email": "mxserviceaccount@mxproxytracking.iam.gserviceaccount.com",
    "client_id": "115383220540349772584",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/mxserviceaccount%40mxproxytracking.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
}

# Configuration
DEFAULT_CONFIG = {
    "developer_token": "4ur5QrkEJKXVB054wqkw",
    "login_customer_id": "6100729843",
    "customer_id": "2061075843",
    "scopes": ["https://www.googleapis.com/auth/adwords"],
}

def get_service_account_credentials():
    """Creates credentials from hardcoded service account JSON."""
    try:
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            json.dump(SERVICE_ACCOUNT_JSON, temp_file)
            temp_file_path = temp_file.name

        credentials = service_account.Credentials.from_service_account_file(
            temp_file_path,
            scopes=DEFAULT_CONFIG["scopes"]
        )
        
        # Clean up temp file
        os.unlink(temp_file_path)
        
        return credentials
    except Exception as e:
        st.error(f"Error loading service account credentials: {str(e)}")
        return None

def get_google_ads_client(developer_token, login_customer_id):
    """Initializes Google Ads client with service account credentials."""
    credentials = get_service_account_credentials()
    if not credentials:
        return None
    
    try:
        client = GoogleAdsClient(
            credentials=credentials,
            developer_token=developer_token,
            login_customer_id=login_customer_id
        )
        return client
    except Exception as e:
        st.error(f"Error initializing Google Ads client: {str(e)}")
        return None

def test_connection(client, customer_id):
    """Tests if the API connection works."""
    try:
        service = client.get_service("GoogleAdsService")
        query = f"SELECT customer.id, customer.descriptive_name FROM customer WHERE customer.id = '{customer_id}'"
        request = client.get_type("SearchGoogleAdsRequest")
        request.customer_id = customer_id
        request.query = query
        
        response = service.search(request=request)
        for row in response:
            return True, f"Success! Connected to account: {row.customer.descriptive_name} (ID: {row.customer.id})"
        
        return False, "No customer data returned"
    except Exception as e:
        return False, f"Connection test failed: {str(e)}"

def fetch_campaigns_data(client, customer_id, start_date, end_date):
    """Fetch Google Ads campaign data for the given date range."""
    try:
        service = client.get_service("GoogleAdsService")
        
        query = f"""
            SELECT 
                campaign.id,
                campaign.name,
                campaign.status,
                campaign.advertising_channel_type,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.conversions,
                segments.date
            FROM campaign
            WHERE campaign.status != 'REMOVED'
            AND segments.date >= '{start_date}'
            AND segments.date <= '{end_date}'
        """
        
        request = client.get_type("SearchGoogleAdsRequest")
        request.customer_id = customer_id
        request.query = query
        
        response = service.search(request=request)
        campaigns = []
        
        for row in response:
            status_name = client.enums.CampaignStatusEnum.CampaignStatus.Name(row.campaign.status)
            type_name = client.enums.AdvertisingChannelTypeEnum.AdvertisingChannelType.Name(row.campaign.advertising_channel_type)

            campaign_data = {
                "Campaign ID": str(row.campaign.id),
                "Campaign Name": row.campaign.name,
                "Status": status_name,
                "Type": type_name,
                "Impressions": row.metrics.impressions,
                "Clicks": row.metrics.clicks,
                "Cost ($)": round(row.metrics.cost_micros / 1_000_000, 2),
                "Conversions": row.metrics.conversions,
                "Date": row.segments.date,
            }
            campaigns.append(campaign_data)
        
        return campaigns, None
    except Exception as e:
        return [], f"Error fetching campaign data: {str(e)}"

# Streamlit App
st.title("🔍 Google Ads API Tester")
st.write("Test your Google Ads API connection and fetch campaign data")

# Sidebar for configuration
st.sidebar.header("Configuration")

# API Configuration
developer_token = st.sidebar.text_input(
    "Developer Token", 
    value=DEFAULT_CONFIG["developer_token"],
    type="password"
)

login_customer_id = st.sidebar.text_input(
    "Login Customer ID", 
    value=DEFAULT_CONFIG["login_customer_id"]
)

customer_id = st.sidebar.text_input(
    "Customer ID", 
    value=DEFAULT_CONFIG["customer_id"]
)

# Date range selection
st.sidebar.subheader("Date Range")
default_start = date.today() - timedelta(days=7)
default_end = date.today() - timedelta(days=1)

start_date = st.sidebar.date_input("Start Date", value=default_start)
end_date = st.sidebar.date_input("End Date", value=default_end)

# Main content
st.header("Service Account Information")
st.json({
    "project_id": SERVICE_ACCOUNT_JSON["project_id"],
    "client_email": SERVICE_ACCOUNT_JSON["client_email"],
    "client_id": SERVICE_ACCOUNT_JSON["client_id"]
})

# Connection Test
st.header("Connection Test")

if st.button("Test Connection", type="primary"):
    with st.spinner("Testing connection..."):
        client = get_google_ads_client(developer_token, login_customer_id)
        
        if client:
            success, message = test_connection(client, customer_id)
            if success:
                st.success(message)
            else:
                st.error(message)
        else:
            st.error("Failed to initialize Google Ads client")

# Data Fetching
st.header("Fetch Campaign Data")

if st.button("Fetch Data", type="secondary"):
    if start_date > end_date:
        st.error("Start date cannot be after end date")
    else:
        with st.spinner("Fetching campaign data..."):
            client = get_google_ads_client(developer_token, login_customer_id)
            
            if client:
                campaigns, error = fetch_campaigns_data(client, customer_id, start_date, end_date)
                
                if error:
                    st.error(error)
                elif campaigns:
                    st.success(f"Successfully fetched {len(campaigns)} campaign records!")
                    
                    # Display data as DataFrame
                    df = pd.DataFrame(campaigns)
                    st.dataframe(df)
                    
                    # Summary metrics
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Total Impressions", f"{df['Impressions'].sum():,}")
                    
                    with col2:
                        st.metric("Total Clicks", f"{df['Clicks'].sum():,}")
                    
                    with col3:
                        st.metric("Total Cost", f"${df['Cost ($)'].sum():.2f}")
                    
                    with col4:
                        st.metric("Total Conversions", f"{df['Conversions'].sum():.1f}")
                    
                    # Download option
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="Download as CSV",
                        data=csv,
                        file_name=f"google_ads_data_{start_date}_to_{end_date}.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("No campaign data found for the selected date range")
            else:
                st.error("Failed to initialize Google Ads client")

# Debug Information
with st.expander("Debug Information"):
    st.write("**Current Configuration:**")
    st.code(f"""
Developer Token: {developer_token[:10]}...
Login Customer ID: {login_customer_id}
Customer ID: {customer_id}
Date Range: {start_date} to {end_date}
Service Account Email: {SERVICE_ACCOUNT_JSON['client_email']}
    """)
    
    st.write("**Requirements:**")
    st.code("""
pip install streamlit google-ads pandas google-auth
    """)
    
    st.write("**Run Command:**")
    st.code("streamlit run google_ads_tester.py")

st.markdown("---")
st.caption("Make sure your service account has the necessary permissions for Google Ads API access.")
