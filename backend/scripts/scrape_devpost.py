"""Scrape Devpost hackathon participants using Playwright.

Usage:
  python scripts/scrape_devpost.py

This will:
1. Launch a visible Chrome browser
2. Navigate to Devpost login → Google OAuth
3. Wait for you to complete Google login (30s timeout)
4. Scrape all participants from the hackathon
5. Save to JSON file + seed Neo4j
"""

import asyncio
import json
import sys
from pathlib import Path

# Add parent to path so we can import app modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

HACKATHON_URL = "https://autonomous-agents-hackathon.devpost.com"
PARTICIPANTS_URL = f"{HACKATHON_URL}/participants"
OUTPUT_FILE = Path(__file__).parent.parent / "participants.json"


async def scrape_participants():
    from playwright.async_api import async_playwright

    print("Launching browser (visible window)...")
    async with async_playwright() as p:
        # Launch with GUI — user_data_dir preserves Google session
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=300,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
        )
        page = await context.new_page()

        # Go to participants page
        print(f"Navigating to {PARTICIPANTS_URL}...")
        await page.goto(PARTICIPANTS_URL, wait_until="networkidle")
        await page.wait_for_timeout(2000)

        # Check if login wall
        content = await page.content()
        if "Please log in" in content:
            print("\n*** LOGIN REQUIRED ***")
            print("Going to Devpost login page directly...")

            # Navigate directly to Devpost sign-in page
            await page.goto("https://devpost.com/users/sign_in", wait_until="networkidle")
            await page.wait_for_timeout(2000)

            # Take screenshot for debugging
            await page.screenshot(path="debug_login.png")
            print(f"Login page URL: {page.url}")

            # List all clickable login options
            all_links = await page.query_selector_all("a, button")
            print("Login options found:")
            for link in all_links:
                t = (await link.text_content() or "").strip()
                h = await link.get_attribute("href") or ""
                c = await link.get_attribute("class") or ""
                if t and ("log" in t.lower() or "sign" in t.lower() or "google" in t.lower() or "oauth" in h.lower()):
                    print(f"  [{t[:40]}] class={c[:30]} href={h[:80]}")

            # Try to click Google OAuth
            google_selectors = [
                'a[href*="google_oauth2"]',
                'a[href*="google"]',
                'button:has-text("Google")',
                'a:has-text("Google")',
                'a.google',
                '.social-login a',
            ]
            clicked = False
            for sel in google_selectors:
                btn = await page.query_selector(sel)
                if btn:
                    visible = await btn.is_visible()
                    if visible:
                        print(f"Clicking: {sel}")
                        await btn.click()
                        clicked = True
                        break

            if not clicked:
                print("Could not find Google button. Please manually log in.")

            print("\n╔══════════════════════════════════════════════════╗")
            print("║  Complete login in the browser window!           ║")
            print("║  Waiting up to 120 seconds...                    ║")
            print("╚══════════════════════════════════════════════════╝\n")

            # Poll for successful login
            for i in range(60):
                await page.wait_for_timeout(2000)
                url = page.url
                if "devpost.com" in url and "sign_in" not in url and "auth" not in url:
                    print(f"Logged in! URL: {url}")
                    break
                if i % 5 == 0:
                    print(f"  Waiting... ({i*2}s) URL: {url[:80]}")

            # Navigate to participants
            print("Going to participants page...")
            await page.goto(PARTICIPANTS_URL, wait_until="networkidle")
            await page.wait_for_timeout(3000)

            # Verify login worked
            new_content = await page.content()
            if "Please log in" in new_content:
                print("ERROR: Still not logged in!")
                await page.screenshot(path="debug_still_locked.png")
                await browser.close()
                return []
            else:
                print("Participants page loaded successfully!")

        # Now scrape participants
        print("\nScraping participants...")

        participants = []
        page_num = 1

        while True:
            print(f"  Page {page_num}...")

            # Wait for participant cards to load
            await page.wait_for_timeout(2000)

            # Extract participant data from the page
            cards = await page.query_selector_all('.participant, .member-card, [class*="participant"], li.member, .software-list-content li, .challenge-participants li')

            if not cards:
                # Try a more generic selector
                cards = await page.query_selector_all('#participants-list li, .participants li, [data-role="participant"]')

            if not cards:
                # Fallback: extract all links that look like user profiles
                all_links = await page.evaluate("""() => {
                    const results = [];
                    const links = document.querySelectorAll('a[href*="devpost.com/"][href$="?ref_content="]');
                    links.forEach(a => {
                        const img = a.querySelector('img');
                        results.push({
                            name: a.textContent.trim(),
                            profile_url: a.href,
                            avatar_url: img ? img.src : ''
                        });
                    });
                    return results;
                }""")

                if not all_links:
                    # Even more generic: find all user profile patterns
                    all_links = await page.evaluate("""() => {
                        const results = [];
                        // Devpost participant cards typically have user avatars and names
                        const items = document.querySelectorAll('.software-list-content a, .participants a, li a');
                        items.forEach(a => {
                            const href = a.href || '';
                            if (href.includes('devpost.com/') && !href.includes('/hackathons') && !href.includes('/software')) {
                                const img = a.querySelector('img') || a.closest('li')?.querySelector('img');
                                const name = a.textContent.trim();
                                if (name && name.length > 1 && name.length < 100) {
                                    results.push({
                                        name: name,
                                        profile_url: href,
                                        avatar_url: img ? img.src : ''
                                    });
                                }
                            }
                        });
                        return results;
                    }""")

                if all_links:
                    participants.extend(all_links)
                    print(f"    Found {len(all_links)} participants via links")
                else:
                    # Last resort: dump the page HTML for debugging
                    html = await page.content()
                    debug_file = Path(__file__).parent.parent / "debug_page.html"
                    debug_file.write_text(html)
                    print(f"    No participants found. Page HTML saved to {debug_file}")

                break
            else:
                for card in cards:
                    name_el = await card.query_selector('a, .name, .member-name, h5, h4, span')
                    img_el = await card.query_selector('img')
                    link_el = await card.query_selector('a[href]')

                    name = await name_el.text_content() if name_el else ""
                    avatar = await img_el.get_attribute("src") if img_el else ""
                    profile = await link_el.get_attribute("href") if link_el else ""

                    if name.strip():
                        participants.append({
                            "name": name.strip(),
                            "profile_url": profile or "",
                            "avatar_url": avatar or "",
                        })

                print(f"    Found {len(cards)} participants on this page")

            # Check for next page
            next_btn = await page.query_selector('a[rel="next"], .next a, .pagination .next')
            if next_btn:
                await next_btn.click()
                await page.wait_for_load_state("networkidle")
                page_num += 1
            else:
                break

        # Deduplicate
        seen = set()
        unique = []
        for p in participants:
            key = p["name"]
            if key not in seen and key:
                seen.add(key)
                unique.append(p)

        print(f"\nTotal unique participants: {len(unique)}")

        # Save to JSON
        OUTPUT_FILE.write_text(json.dumps(unique, indent=2))
        print(f"Saved to {OUTPUT_FILE}")

        # Print first 10
        for i, p in enumerate(unique[:10]):
            print(f"  {i+1}. {p['name']} | {p.get('avatar_url', '')[:60]}")

        await browser.close()
        return unique


async def main():
    participants = await scrape_participants()

    if not participants:
        print("No participants found. Exiting.")
        return

    # Seed Neo4j
    print("\nSeeding Neo4j...")
    from app.services.graph_service import get_neo4j, _id

    neo4j = await get_neo4j()
    await neo4j.execute_write("MATCH (n) DETACH DELETE n", {})

    colors = ["#6366f1", "#10b981", "#8b5cf6", "#f59e0b", "#ef4444",
              "#3b82f6", "#ec4899", "#14b8a6", "#f97316", "#06b6d4"]

    # Create event
    await neo4j.execute_write(
        "CREATE (e:Event {url: $url, title: 'Autonomous Agents Hackathon', "
        "id: $id, date: '2026-02-27', location: 'AWS Builder Loft, SF', "
        "source: 'devpost', event_type: 'hackathon', participants: $count})",
        {"url": HACKATHON_URL, "id": _id(), "count": len(participants)},
    )

    # Create "Me" node
    await neo4j.execute_write(
        "CREATE (u:Person {id: 'me', name: 'Me', title: 'Hacker', company: 'NEXUS', "
        "role: 'self', avatar_color: '#f97316', connection_score: 100, is_self: true}) "
        "WITH u MATCH (e:Event {url: $url}) CREATE (u)-[:ATTENDED]->(e)",
        {"url": HACKATHON_URL},
    )

    # Create participant nodes
    for i, p in enumerate(participants):
        pid = _id()
        avatar = p.get("avatar_url", "")
        await neo4j.execute_write(
            "CREATE (p:Person {id: $id, name: $name, profile_url: $profile, "
            "avatar_url: $avatar, avatar_color: $color, "
            "connection_score: $score, is_self: false, role: 'participant'}) "
            "WITH p MATCH (e:Event {url: $url}) CREATE (p)-[:ATTENDED]->(e)",
            {
                "id": pid, "name": p["name"],
                "profile": p.get("profile_url", ""),
                "avatar": avatar,
                "color": colors[i % len(colors)],
                "score": max(40, 95 - i),  # Rough initial ranking
                "url": HACKATHON_URL,
            },
        )

    # Connect me to all
    await neo4j.execute_write(
        "MATCH (me:Person {id: 'me'}), (p:Person) WHERE p.id <> 'me' "
        "CREATE (me)-[:CONNECTED_TO {strength: p.connection_score * 0.8, source: 'event'}]->(p)",
        {},
    )

    await neo4j.disconnect()
    print(f"Seeded {len(participants)} participants into Neo4j!")


if __name__ == "__main__":
    asyncio.run(main())
