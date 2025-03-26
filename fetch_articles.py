import requests
import firebase_admin
from firebase_admin import credentials, firestore, storage
from datetime import datetime
import xml.etree.ElementTree as ET
import os
import time

# -------------------------- CONFIG --------------------------
IEEE_API_KEY = "gzsxnqj5tmr3eb92x9w46rrw"
SERP_API_KEY = "1ac29f85d1c0b690a683e756ddfca1d8874b0c817cd1648bf1072e7d0b2d809a"
FIREBASE_JSON = "config/pathmaster-327b2-firebase-adminsdk-fbsvc-708e63f7c0.json"

# -------------------------- FIREBASE INIT --------------------------
cred = credentials.Certificate(FIREBASE_JSON)
firebase_admin.initialize_app(cred)
db = firestore.client()

# === CATÉGORIES ===
CATEGORIES = {
    "Perception & Vision": ["vision", "perception", "scene understanding"],
    "Planning & Decision": ["motion planning", "decision making", "reasoning"],
    "Human-Robot Interaction": ["human interaction", "language grounding"],
    "Multi-Agent Systems": ["multi-agent", "coordination", "collaboration"],
    "Embodied Intelligence": ["embodiment", "actuation", "sensors"]
}

# === ARXIV SCRAPER ===
def scrape_arxiv():
    all_articles = []
    for cat, keywords in CATEGORIES.items():
        query = " + ".join([f"{kw}+LLM+robotics" for kw in keywords])
        url = f"http://export.arxiv.org/api/query?search_query=all:{query}&max_results=5"
        res = requests.get(url)
        root = ET.fromstring(res.content)

        for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
            title = entry.find("{http://www.w3.org/2005/Atom}title").text.strip()
            abstract = entry.find("{http://www.w3.org/2005/Atom}summary").text.strip()
            link = entry.find("{http://www.w3.org/2005/Atom}id").text.strip()
            pdf_link = link.replace("abs", "pdf") + ".pdf"

            all_articles.append({
                "title": title,
                "abstract": abstract,
                "url": link,
                "pdf_url": pdf_link,
                "category": cat,
                "website": "arXiv"
            })
    return all_articles

# === IEEE SCRAPER ===
def scrape_ieee():
    all_articles = []
    for cat, keywords in CATEGORIES.items():
        for kw in keywords:
            query = f"{kw} LLM robotics"
            url = f"https://ieeexploreapi.ieee.org/api/v1/search/articles?apikey={IEEE_API_KEY}&format=json&max_records=5&start_record=1&sort_order=desc&abstract={query}"
            res = requests.get(url)
            if res.status_code != 200:
                continue
            data = res.json()
            for item in data.get("articles", []):
                all_articles.append({
                    "title": item.get("title", ""),
                    "abstract": item.get("abstract", ""),
                    "url": item.get("html_url", ""),
                    "pdf_url": item.get("pdf_url", ""),
                    "category": cat,
                    "website": "IEEE Xplore"
                })
            time.sleep(1)
    return all_articles

# === GOOGLE SCHOLAR VIA SERPAPI ===
def scrape_google_scholar():
    all_articles = []
    for cat, keywords in CATEGORIES.items():
        for kw in keywords:
            query = f"{kw} LLM robotics"
            url = f"https://serpapi.com/search.json?q={query}&engine=google_scholar&api_key={SERP_API_KEY}"
            res = requests.get(url)
            if res.status_code != 200:
                continue
            results = res.json().get("organic_results", [])
            for result in results:
                all_articles.append({
                    "title": result.get("title", ""),
                    "abstract": result.get("snippet", ""),
                    "url": result.get("link", ""),
                    "pdf_url": result.get("resources", [{}])[0].get("link", "") if result.get("resources") else "",
                    "category": cat,
                    "website": "Google Scholar"
                })
            time.sleep(1)
    return all_articles

# === FIRESTORE UPLOAD ===
def upload_to_firestore(articles):
    for art in articles:
        db.collection("articles").add(art)
    print(f"✅ {len(articles)} articles ajoutés à Firestore")

# === MAIN EXEC ===
def main():
    arxiv = scrape_arxiv()
    ieee = scrape_ieee()
    scholar = scrape_google_scholar()

    all_data = arxiv + ieee + scholar
    upload_to_firestore(all_data)

if __name__ == "__main__":
    main()
