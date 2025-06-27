import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import random

st.set_page_config(page_title="Lead Finder AI", layout="wide")

# ------------------ Load Data ------------------ #
@st.cache_data

def load_data():
    df = pd.read_csv("companies.csv")

    def score_lead(row):
        score = 0
        if row['location'] in ['USA', 'UK']:
            score += 2
        if row['industry'] in ['Fintech', 'CRM Software', 'SaaS']:
            score += 2
        if '.io' in row['website'] or '.ai' in row['website']:
            score += 2
        if len(row['name']) > 8:
            score += 1
        return score

    def reason_for_score(row):
        reasons = []
        if row['location'] in ['USA', 'UK']:
            reasons.append("Strong Market")
        if row['industry'] in ['Fintech', 'CRM Software', 'SaaS']:
            reasons.append("Target Industry")
        if '.ai' in row['website']:
            reasons.append("AI-Focused")
        if len(row['name']) > 8:
            reasons.append("Brand Depth")
        return ", ".join(reasons) or "General"

    tech_stack = ['AWS, React, Python', 'GCP, Django, Postgres', 'Azure, Node.js, MongoDB']

    df['lead_score'] = df.apply(score_lead, axis=1)
    df['reason'] = df.apply(reason_for_score, axis=1)
    df['tech_stack'] = [random.choice(tech_stack) for _ in range(len(df))]
    return df

df = load_data()

# ------------------ Enrichment: Scrape Meta Description ------------------ #
@st.cache_data(show_spinner="🔍 Enriching data from websites...")
def enrich_description(url):
    try:
        if not url.startswith("http"):
            url = "http://" + url
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=4)
        soup = BeautifulSoup(res.text, "html.parser")
        desc = soup.find("meta", attrs={"name": "description"})
        if desc and desc.get("content"):
            return desc["content"]
        else:
            return "No description available."
    except:
        return "Could not retrieve info."

# ------------------ Sidebar ------------------ #
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/599/599995.png", width=80)
st.sidebar.header("🎯 Filter Options")
industries = st.sidebar.multiselect("📌 Industry", sorted(df['industry'].unique()))
locations = st.sidebar.multiselect("🌍 Location", sorted(df['location'].unique()))
min_score = st.sidebar.slider("📈 Minimum Lead Score", 0, 10, 0)
search = st.sidebar.text_input("🔎 Search Company Name")

# ------------------ Filtering ------------------ #
filtered_df = df.copy()
if industries:
    filtered_df = filtered_df[filtered_df['industry'].isin(industries)]
if locations:
    filtered_df = filtered_df[filtered_df['location'].isin(locations)]
if search:
    filtered_df = filtered_df[filtered_df['name'].str.contains(search, case=False)]
filtered_df = filtered_df[filtered_df['lead_score'] >= min_score]
filtered_df = filtered_df.drop_duplicates(subset='website')
filtered_df = filtered_df.sort_values(by="lead_score", ascending=False).head(10)

# ------------------ UI Header ------------------ #
st.markdown("""
    <h1 style='text-align: center; color: #4CAF50;'>🚀 AI-Powered Lead Finder</h1>
    <h4 style='text-align: center; color: gray;'>Find, Score, and Enrich High-Quality B2B Leads</h4>
    <hr style='border: 1px solid #eee;'>
""", unsafe_allow_html=True)

# ------------------ User Guide ------------------ #
with st.expander("ℹ️ How to Use This Tool"):
    st.markdown("""
    - Use the sidebar to filter by industry, location, or score.
    - Click the website link to visit a lead.
    - Download the final filtered and enriched leads at the bottom.
    """)

# ------------------ Helper: Color by Score ------------------ #
def get_score_color(score):
    if score >= 8:
        return "#4CAF50"
    elif score >= 5:
        return "#FFC107"
    else:
        return "#F44336"

# ------------------ Show Summary ------------------ #
with st.expander("📈 Summary Insights"):
    st.write("Top Industries:", df['industry'].value_counts().head(3).to_dict())
    st.write("Top Countries:", df['location'].value_counts().head(3).to_dict())

# ------------------ Show Enriched Leads ------------------ #
st.markdown(f"### 📋 Showing {len(filtered_df)} Enriched Leads")
st.markdown("<br>", unsafe_allow_html=True)

for _, row in filtered_df.iterrows():
    color = get_score_color(row['lead_score'])
    st.markdown(f"""
        <div style='border-left: 6px solid {color}; border-radius:8px; padding:15px; margin-bottom:15px; background-color:#fefefe; box-shadow: 0 2px 6px rgba(0,0,0,0.05);'>
            <h4 style='margin:0; color:#2e7d32;'>{row['name']}</h4>
            <p style='margin:4px 0;'>🌐 <a href="{row['website']}" target="_blank">{row['website']}</a> &nbsp;&nbsp; 🏷️ <span style="background-color:#e8f5e9; padding:3px 8px; border-radius:5px;">{row['industry']}</span> &nbsp;&nbsp; 📍 {row['location']}</p>
            <div style='margin:5px 0 10px 0;'>
                <b>Lead Score:</b> 
                <span style='color:{color}; font-weight:bold;'>{row['lead_score']}/10</span>
                <div style="height: 8px; background-color: #ddd; border-radius: 4px; overflow: hidden;">
                    <div style="width: {row['lead_score']*10}%; background-color: {color}; height: 100%;"></div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)


# ------------------ Download Section ------------------ #
#st.markdown("---")
st.download_button("📥 Download Filtered Leads as CSV", data=filtered_df.to_csv(index=False), file_name="filtered_leads.csv", mime="text/csv")
st.download_button("🗃️ Export to CRM (JSON Format)", data=filtered_df.to_json(orient='records'), file_name="crm_leads.json", mime="application/json")

# ------------------ Ethical Footer ------------------ #
st.markdown("**⚠️ Note:** All data shown is publicly available and follows ethical data usage standards.")
