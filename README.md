# my.packhunter
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
