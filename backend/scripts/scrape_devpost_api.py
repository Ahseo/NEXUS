#!/usr/bin/env python3
"""Scrape Devpost participants using requests + cookies.

This script uses session cookies from a logged-in browser session.
Export cookies from Chrome DevTools or use browser extension.
"""

import json
import re
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

HACKATHON_URL = "https://autonomous-agents-hackathon.devpost.com"
PARTICIPANTS_URL = f"{HACKATHON_URL}/participants"
OUTPUT_FILE = Path(__file__).parent.parent / "participants.json"

# Get cookies from browser DevTools > Application > Cookies
# Copy the cookie string from document.cookie or export as JSON
COOKIES = {
    # Add your Devpost session cookies here
    # "_devpost_session": "your_session_cookie",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": HACKATHON_URL,
}


def scrape_participants():
    """Scrape all participants from Devpost hackathon page."""
    participants = []
    page = 1
    
    with httpx.Client(cookies=COOKIES, headers=HEADERS, follow_redirects=True) as client:
        while True:
            url = f"{PARTICIPANTS_URL}?page={page}"
            print(f"Fetching page {page}...")
            
            resp = client.get(url)
            if resp.status_code != 200:
                print(f"Error: {resp.status_code}")
                break
            
            soup = BeautifulSoup(resp.text, "html.parser")
            
            # Check if login required
            if "Please log in" in resp.text:
                print("ERROR: Login required. Add session cookies to the script.")
                print("1. Login to Devpost in your browser")
                print("2. Open DevTools > Application > Cookies")
                print("3. Copy _devpost_session cookie value")
                print("4. Add it to COOKIES dict in this script")
                return []
            
            # Find participant cards
            cards = soup.select(".software-list-content li, .participant, .member-card")
            
            if not cards:
                # Try alternative selectors
                cards = soup.select("li.member, [class*='participant']")
            
            if not cards:
                print(f"No more participants found on page {page}")
                break
            
            for card in cards:
                # Extract name
                name_el = card.select_one("a, .name, h5, span")
                name = name_el.get_text(strip=True) if name_el else ""
                
                # Extract profile URL
                link_el = card.select_one("a[href]")
                profile_url = link_el.get("href", "") if link_el else ""
                if profile_url and not profile_url.startswith("http"):
                    profile_url = f"https://devpost.com{profile_url}"
                
                # Extract avatar
                img_el = card.select_one("img")
                avatar_url = img_el.get("src", "") if img_el else ""
                
                if name and len(name) > 1:
                    participants.append({
                        "name": name,
                        "profile_url": profile_url,
                        "avatar_url": avatar_url,
                    })
            
            print(f"Found {len(cards)} on page {page}, total: {len(participants)}")
            
            # Check for next page
            next_link = soup.select_one('a[rel="next"], .next a, .pagination .next')
            if not next_link:
                break
            
            page += 1
    
    # Dedupe
    seen = set()
    unique = []
    for p in participants:
        key = p["name"]
        if key not in seen:
            seen.add(key)
            unique.append(p)
    
    print(f"\nTotal unique participants: {len(unique)}")
    
    # Save
    OUTPUT_FILE.write_text(json.dumps(unique, indent=2))
    print(f"Saved to {OUTPUT_FILE}")
    
    return unique


def extract_profile_details(profile_url: str) -> dict:
    """Extract detailed info from a Devpost profile page."""
    with httpx.Client(cookies=COOKIES, headers=HEADERS, follow_redirects=True) as client:
        resp = client.get(profile_url)
        if resp.status_code != 200:
            return {}
        
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Extract SNS links
        sns = {}
        for link in soup.select("a[href]"):
            href = link.get("href", "")
            if "linkedin.com" in href:
                sns["linkedin"] = href
            elif "github.com" in href:
                sns["github"] = href
            elif "twitter.com" in href or "x.com" in href:
                sns["twitter"] = href
        
        # Extract skills
        skills = []
        for tag in soup.select(".tag, .skill, [class*='skill']"):
            skills.append(tag.get_text(strip=True))
        
        return {"sns": sns, "skills": skills}


if __name__ == "__main__":
    participants = scrape_participants()
    
    if participants:
        # Print first 10
        for i, p in enumerate(participants[:10]):
            print(f"{i+1}. {p['name']}")
