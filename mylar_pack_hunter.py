#!/usr/bin/env python3
import os
import re
import sqlite3
import time
import urllib.parse
import urllib.request
from urllib.error import HTTPError
from bs4 import BeautifulSoup
import myjdapi

# ==========================================
#               CONFIGURATION
# ==========================================

# Path to your Mylar database 
MYLAR_DB_PATH = "/appdata/mylar/mylar.db"

# MyJDownloader Credentials
MYJD_EMAIL = "your_email@example.com"
MYJD_PASSWORD = "your_password"
MYJD_DEVICE_NAME = "Your_JD2_Device_Name" # Must match exactly what is in MyJDownloader

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

# ==========================================

def get_missing_series(db_path):
    if not os.path.exists(db_path):
        print(f"[!] DB not found at: {db_path}")
        print("[!] Please check your MYLAR_DB_PATH configuration.")
        return []

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    query = """
        SELECT s.ComicName, s.ComicYear, COUNT(i.IssueID) as MissingCount
        FROM comics s
        JOIN issues i ON s.ComicID = i.ComicID
        WHERE i.Status = 'Wanted'
        GROUP BY s.ComicID
        HAVING MissingCount > 0
    """
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    return results

def search_getcomics(comic_name, comic_year):
    clean_name = re.sub(r'[^\w\s]', '', comic_name)
    query = f"{clean_name} {comic_year}"
    search_url = f"https://getcomics.org/?s={urllib.parse.quote(query)}"
    
    req = urllib.request.Request(search_url, headers={"User-Agent": USER_AGENT})
    
    max_retries = 3
    html = ""
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req) as response:
                html = response.read().decode('utf-8')
                break  
        except HTTPError as e:
            if e.code == 429:
                wait_time = (attempt + 1) * 10 
                print(f"    [!] Rate limited (429). Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            else:
                print(f"    [!] Connection failed for {clean_name}: {e}")
                return []
        except Exception as e:
            print(f"    [!] Connection failed for {clean_name}: {e}")
            return []
    else:
        print(f"    [!] Skipping {clean_name} after {max_retries} rate limit failures.")
        return []

    soup = BeautifulSoup(html, 'html.parser')
    matches = []
    
    for post in soup.find_all('article'):
        title_tag = post.find('h1', class_='post-title') or post.find('h2', class_='post-title')
        if not title_tag or not title_tag.find('a'): continue
        
        a_tag = title_tag.find('a')
        title_text = a_tag.get_text(strip=True)
        link = a_tag['href']

        if any(re.search(pat, title_text, re.IGNORECASE) for pat in [r'vol', r'tpb', r'collection', r'compendium', r'\d+-\d+', r'complete']):
            matches.append({'title': title_text, 'url': link})
            
    return matches

def main():
    print("=====================================")
    print("   MYLAR GETCOMICS PACK HUNTER")
    print("=====================================\n")
    
    series = get_missing_series(MYLAR_DB_PATH)
    if not series:
        print("[*] No missing issues found in Mylar. Exiting.")
        return

    found_packs = []
    print(f"[*] Scanning GetComics for {len(series)} missing series...")
    print("[*] A 3-second delay is added between searches to prevent rate limiting.\n")
    
    for name, year, count in series:
        packs = search_getcomics(name, year)
        if packs:
            print(f"[+] {name} ({year}) - {count} missing")
            for p in packs:
                print(f"    -> {p['title']}")
                found_packs.append(p)
        
        time.sleep(3)

    if not found_packs:
        print("\n[-] No relevant packs found on GetComics.")
        return

    print(f"\n[*] Found {len(found_packs)} potential packs.")
    
    backup_file = os.path.join(os.path.dirname(__file__), "found_packs_backup.txt")
    try:
        with open(backup_file, "w") as f:
            for p in found_packs:
                f.write(f"{p['url']}\n")
        print(f"[*] Backup of all links saved to: {backup_file}")
    except Exception as e:
        print(f"[!] Could not save backup file: {e}")

    choice = input("\nSend these directly to JDownloader2 LinkGrabber? [y/N]: ")
    
    if choice.lower() == 'y':
        print("\n[*] Connecting to MyJDownloader API...")
        jd = myjdapi.Myjdapi()
        jd.set_app_key("MylarPackHunter")
        try:
            jd.connect(MYJD_EMAIL, MYJD_PASSWORD)
            device = jd.get_device(MYJD_DEVICE_NAME)
            
            urls = [p['url'] for p in found_packs]
            batch_size = 50 
            
            for i in range(0, len(urls), batch_size):
                batch = urls[i:i + batch_size]
                part_num = (i // batch_size) + 1
                
                device.linkgrabber.add_links([{
                    "autostart": False, 
                    "links": "\n".join(batch),
                    "packageName": f"Mylar Pack Hunter Finds (Batch {part_num})",
                    "priority": "HIGH"
                }])
                print(f"  [+] Successfully pushed Batch {part_num} ({len(batch)} links) to LinkGrabber!")
                time.sleep(2) 
                
            print("\n[*] All batches complete. Check your JD2 UI.")
        except Exception as e:
            print(f"\n[!] MyJDownloader push failed: {e}")
            print(f"[*] Don't worry, your links are safe. You can manually load '{backup_file}' into JDownloader2.")
    else:
        print("[*] Aborted. No links sent.")

if __name__ == "__main__":
    main()
