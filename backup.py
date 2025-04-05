import os
import requests as re
import urllib
import thread_reader as tr
from bs4 import BeautifulSoup


def download_image(img_url, save_folder):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": img_url  # Some websites need this to allow downloads
    }

    filename = os.path.basename(urllib.parse.urlparse(img_url).path)
    if not filename:
        print(f"Skipping invalid image URL: {img_url}")
        return None

    save_path = os.path.join(save_folder, filename)

    try:
        response = re.get(img_url, headers=headers, stream=True)
        if response.status_code == 200:
            with open(save_path, "wb") as img_file:
                for chunk in response.iter_content(1024):
                    img_file.write(chunk)
            return filename
        else:
            print(f"Failed to download {img_url} (Status: {response.status_code})")
    except Exception as e:
        print(f"Error downloading {img_url}: {e}")

    return None


def process_images(html, base_url, thread_link):
    soup = BeautifulSoup(html, "html.parser")
    for img in soup.find_all("img"):
        img_url = urllib.parse.urljoin(base_url, img["src"])  # Get full URL
        local_filename = download_image(img_url, f"{thread_link}/images")
        if local_filename:
            img["src"] = f"../images/{local_filename}"  # Replace src
    return soup.prettify()


def download_css(css_url, save_folder):
    filename = os.path.basename(urllib.parse.urlparse(css_url).path)
    save_path = os.path.join(save_folder, filename)

    try:
        response = re.get(css_url)
        if response.status_code == 200:
            with open(save_path, "w", encoding="utf-8") as css_file:
                css_file.write(response.text)
            return filename  # Return the local filename
    except Exception as e:
        print(f"Failed to download {css_url}: {e}")
    return None


def process_thread_links(html, base_url, thread_link):
    soup = BeautifulSoup(html, "html.parser")

    for link in soup.findall("ul", class_=["pg"]):
        print(1)


def process_css(html, base_url, thread_link):
    soup = BeautifulSoup(html, "html.parser")
    for link in soup.find_all("link", rel="stylesheet"):
        css_url = urllib.parse.urljoin(base_url, link["href"])
        local_filename = download_css(css_url, f"{thread_link}/css")
        if local_filename:
            link["href"] = f"../css/{local_filename}"  # Update link
    return soup.prettify()


def main():
    thread_link = input("Paste thread to backup here:")

    first_page = tr.fetch_html(thread_link)
    page_count = tr.get_total_pages(first_page)
    thread_title = tr.get_thread_title(first_page)

    print(f"Found {page_count} pages for {thread_title}.")

    os.makedirs(f"{thread_title}/html", exist_ok=True)
    os.makedirs(f"{thread_title}/css", exist_ok=True)
    os.makedirs(f"{thread_title}/images", exist_ok=True)

    for page in range(1, page_count + 1):
        page_url = f"{thread_link}/{page}" if page > 1 else thread_link
        print(f"Fetching page {page} from {page_url}")

        page_html = tr.fetch_html(page_url)

        # Process images and CSS
        updated_html = process_images(page_html.prettify(), page_url, thread_title)
        updated_html = process_css(updated_html, page_url, thread_title)
        updated_html = process_thread_links(updated_html, page_url, thread_title)

        # Save HTML
        with open(f"{thread_title}/html/{page}.html", "w", encoding="utf-8") as fil:
            fil.write(updated_html)

    print("Full backup complete!")


if __name__ == "__main__":
    main()
