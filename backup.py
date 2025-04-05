import os
import requests as re
import urllib
from bs4 import BeautifulSoup
import thread_reader as tr

# Function to sanitize the folder name
def sanitize_folder_name(name):
    import re 
    return re.sub(r'[\\/*?:"<>|]', "_", name)  # Replace invalid characters with underscores

# Function to download images and return the local filename
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


# Function to process and update image URLs in HTML (including avatars)
def process_images(html, base_url, thread_link):
    soup = BeautifulSoup(html, "html.parser")

    for img in soup.find_all("img"):
        img_url = None

        # Handle lazy-loaded images
        if img.has_attr("data-src"):
            img_url = urllib.parse.urljoin(base_url, img["data-src"])  # Use data-src if present
        elif img.has_attr("src"):
            img_url = urllib.parse.urljoin(base_url, img["src"])  # Fallback to src

        if not img_url or "pix.gif" in img_url:  # Skip placeholders
            continue

        # Identify if it's an avatar by checking its URL structure
        if "/img/users/avatar/" in img_url:
            save_folder = os.path.join(thread_link, "images/avatars")
            new_src = f"../images/avatars/{os.path.basename(img_url)}"
        else:
            save_folder = os.path.join(thread_link, "images")
            new_src = f"../images/{os.path.basename(img_url)}"

        # Download the image
        local_filename = download_image(img_url, save_folder)
        if local_filename:
            img["src"] = new_src  # Update src to local path

            # Remove data-src to prevent lazy loading from interfering
            if img.has_attr("data-src"):
                del img["data-src"]

    return soup.prettify()

# Function to download CSS and return the local filename
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

# Function to update CSS links in HTML
def process_css(html, base_url, thread_link):
    soup = BeautifulSoup(html, "html.parser")
    for link in soup.find_all("link", rel="stylesheet"):
        css_url = urllib.parse.urljoin(base_url, link["href"])
        local_filename = download_css(css_url, f"{thread_link}/css")
        if local_filename:
            link["href"] = f"../css/{local_filename}"  # Update link
    return soup.prettify()


def process_thread_links(html, base_url, thread_title, page_number, page_count):
    soup = BeautifulSoup(html, "html.parser")
    
    for link in soup.find_all("a", href=True):
        link_url = link["href"]
        
        # Skip avatar links and user profile links
        if "/id/" in link_url or "/img/users/avatar/" in link_url:
            continue  

        # Convert relative URLs to absolute URLs
        full_url = urllib.parse.urljoin(base_url, link_url)

        # Ensure it's a pagination link (within the same thread)
        if thread_title in full_url and full_url != base_url:
            page_num = extract_page_number(full_url)  # Extract the page number

            if page_num:
                # Ensure the link correctly references local HTML files
                link["href"] = f"../html/{page_num}.html"

    return soup.prettify()


# Helper function to extract the page number from the URL
def extract_page_number(url):
    try:
        # The page number is assumed to be the last part of the URL (after the last slash)
        page_num = int(url.rstrip('/').split('/')[-1])  # Get the last part of the URL
        return page_num
    except ValueError:
        return None


def main():
    thread_link = input("Paste thread to backup here:")

    # Fetch the first page to extract total pages and title
    first_page = tr.fetch_html(thread_link)
    page_count = tr.get_total_pages(first_page)
    thread_title = tr.get_thread_title(first_page)

    # Sanitize the thread title to create valid folder names
    sanitized_title = sanitize_folder_name(thread_title)

    print(f"Found {page_count} pages for {thread_title}.")

    # Create the necessary directories for backup using sanitized title
    os.makedirs(f"{sanitized_title}/html", exist_ok=True)
    os.makedirs(f"{sanitized_title}/css", exist_ok=True)
    os.makedirs(f"{sanitized_title}/images", exist_ok=True)
    os.makedirs(f"{sanitized_title}/images/avatars", exist_ok=True)

    # Loop through each page of the thread
    for page in range(1, page_count + 1):
        page_url = f"{thread_link}/{page}" if page > 1 else thread_link
        print(f"Fetching page {page} from {page_url}")

        page_html = tr.fetch_html(page_url)

        # Process images, CSS, and thread links (pagination)
        updated_html = process_images(page_html.prettify(), page_url, sanitized_title)
        updated_html = process_css(updated_html, page_url, sanitized_title)
        updated_html = process_thread_links(updated_html, page_url, sanitized_title, page, page_count)

        # Save the updated HTML to the respective page file
        with open(f"{sanitized_title}/html/{page}.html", "w", encoding="utf-8") as fil:
            fil.write(updated_html)

    print("Full backup complete!")


# Run the main function
if __name__ == "__main__":
    main()
