# Mylar GetComics Pack Hunter

A Python script that reads your Mylar SQLite database, identifies series with missing (Wanted) issues, and automatically scrapes GetComics for bulk compilation packs (Vol, TPB, Omnibus, complete runs, etc.). 

Instead of downloading single issues one-by-one via Mylar's internal DDL, this script pushes bulk packs directly to your **JDownloader2 LinkGrabber** via the MyJDownloader API for your manual review and approval. 

## Features
* **Direct DB Querying:** Reads `mylar.db` directly to find exactly what you are missing.
* **Regex Pack Filtering:** Only grabs posts containing pack indicators (Vol, TPB, Compendium, Issue Ranges).
* **Anti-Ban Pacing:** Includes a 3-second delay between queries and automatic retry scaling to bypass Cloudflare 429 Too Many Requests errors.
* **API Batching:** Pushes links to JD2 in chunks of 50 to avoid API timeout crashes.
* **Failsafe Backups:** Automatically saves a local `.txt` file containing all found URLs before attempting to contact the JD2 API.
* **Interactive Control:** Pushes to the JD2 LinkGrabber tab but does *not* auto-start downloads, allowing you to curate the results.

## Requirements

Ensure Python 3 is installed in your environment, along with these packages:
```bash
pip install beautifulsoup4 myjdapi


It is a targeted web scraper and API bridge. Here is the exact mechanical breakdown of what happens when you hit enter:

1. Database Query
It connects directly to your local mylar.db SQLite file. It runs a query to find every comic series where you have at least one issue marked as "Wanted," bundles them by series, and outputs a list of the series name, the release year, and how many issues you are missing.

2. The Web Scrape
For every series on that list, it strips out special characters from the title and sends a search query to GetComics.

It uses BeautifulSoup to parse the raw HTML of the search results page.

It scans the title of every post on that page using regular expressions (regex). It is specifically looking for titles that contain words like "Vol", "TPB", "Collection", "Compendium", "Complete", or a number range like "01-50".

If a post matches, it grabs the URL.

3. Rate Limiting
Because searching hundreds of series back-to-back looks like a DDoS attack, the script pauses for 3 seconds between every search. If GetComics still blocks it with a 429 (Too Many Requests) error, the script automatically pauses for 10 seconds, then 20, then 30, retrying each time before giving up on that specific comic.

4. The Local Backup
Once the scrape finishes, it takes every single URL it successfully matched and writes them to a standard text file called found_packs_backup.txt on your OpenMediaVault drive. This ensures that if the next step fails, your 30-minute scrape wasn't wasted.

5. The JDownloader2 Push
It stops and asks for your permission. If you type 'y', it logs into your MyJDownloader account via their API.

It takes your list of URLs and slices them into chunks of 50.

It sends each chunk to your JDownloader2 instance with a 2-second pause in between, bypassing the API's 3-second timeout limit.

It dumps all the links into your LinkGrabber tab and sets autostart to False, meaning nothing downloads until you look at the JD2 interface and manually click start.

Download mylar_pack_hunter.py and place it in your preferred directory (e.g., inside a scripts folder in your Mylar appdata).

Open the script in a text editor and update the CONFIGURATION block at the top of the file:

MYLAR_DB_PATH: Set this to the path of your mylar.db file (default is /appdata/mylar/mylar.db).

MYJD_EMAIL: Your MyJDownloader email address.

MYJD_PASSWORD: Your MyJDownloader password.

MYJD_DEVICE_NAME: The exact device name configured in your JD2 interface.

Run the script interactively from your terminal.

If running natively on the host OS:

Bash
python3 mylar_pack_hunter.py
If running inside a Docker container (recommended):

Bash
docker exec -it mylar python3 /path/to/your/scripts/mylar_pack_hunter.py
The Workflow
The script will scan the database and output the series being checked.

It will query GetComics with a 3-second delay between titles.

Once the scan completes, a local backup file (found_packs_backup.txt) is generated in the same folder as the script.

You will be prompted: Send these directly to JDownloader2 LinkGrabber? [y/N]:

Type y and press Enter. The script will batch-send the links to your JD2 instance.

Open your JDownloader2 interface, review the packages in LinkGrabber, and click Start Downloads. Mylar's Folder Monitor will sweep the completed files into your library automatically.
