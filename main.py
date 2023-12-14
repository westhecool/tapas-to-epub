from bs4 import BeautifulSoup
import os
from ebooklib import epub
from PIL import Image
import argparse
import shutil
import requests
import io
import re

args = argparse.ArgumentParser()
args.description = 'Download and convert a whole tapas series to epub.'
args.add_argument('link', help='Link to tapas comic to download. (This should be the link to chapter list.)', type=str)
args.add_argument('--clean-up', help='Clean up the downloaded images after they are put in the epub.', type=bool, default=True, action=argparse.BooleanOptionalAction)
args.add_argument('--download-nsfw', help='Download NSFW chapters.', type=bool, default=False, action=argparse.BooleanOptionalAction)
args.add_argument('--split-into-parts', help='Split the comic into parts.', type=bool, default=False, action=argparse.BooleanOptionalAction)
args.add_argument('--chapters-per-part', help='Chapters per part. (Default: 100)', type=int, default=100)
args = args.parse_args()

def make_safe_filename_windows(filename):
    illegal_chars = r'<>:"/\|?*'
    for char in illegal_chars:
        filename = filename.replace(char, "_")
    return filename

def getNumericIndex(filename:str):
    return int(filename.split('.')[0])

def downloadChapter(link, title, chapterid):
    html = requests.get(link, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 OPR/105.0.0.0"}).text
    soup = BeautifulSoup(html, "html.parser")
    imglist = soup.find(class_="viewer__body").findChildren("img")
    i2 = 0
    if not os.path.exists(f'data/{make_safe_filename_windows(title)}/{chapterid}'):
        os.makedirs(f'data/{make_safe_filename_windows(title)}/{chapterid}')
    for img in imglist:
        i2 += 1
        print(f'\rDownloading image {i2}/{len(imglist)}', end='')
        img = requests.get(img["data-src"], headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 OPR/105.0.0.0"}).content
        image = Image.open(io.BytesIO(img))
        image = image.convert('RGB')
        image.save(f"data/{make_safe_filename_windows(title)}/{chapterid}/{i2}.jpg")
    print('')

def downloadComic(link):
    r = requests.get(link, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 OPR/105.0.0.0"})
    soup = BeautifulSoup(r.text, "html.parser")
    cid = ""
    for x in soup.find_all("meta"):
        if x.get("property") == "al:android:url":
            cid = x.get("content").split("tapastic://series/")[1].split("/info")[0]
    title = soup.find(class_="title").text.strip()
    authors = ""
    for x in soup.find(class_="creator-section").find_all(class_="creator-info__top"):
        authors += x.find(class_="name").text.strip() + ", "
    authors = authors[:-2]

    print(f"Title: {title}")
    print(f"ID: {cid}")
    print(f"Authors: {authors}")

    try:
        shutil.rmtree(f"data/{make_safe_filename_windows(title)}")
    except:
        pass

    chapters = []
    i = 1
    while True:
        r = requests.get(f"https://tapas.io/series/{cid}/episodes?page={i}&sort=OLDEST&init_load=0&large=true&last_access=0", headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 OPR/105.0.0.0"}).json()
        if len(r["data"]["episodes"]) > 0:
            print(f"\rFetching chapters from page {i}", end="")
            chapters.extend(r["data"]["episodes"])
            i += 1
        else:
            print("")
            break

    print(f"Chapter count: {len(chapters)}")

    book = epub.EpubBook()
    if args.split_into_parts:
        book.set_title(f"{title} - Part 1")
    else:
        book.set_title(title)
    book.add_author(authors)
    book.spine = ["nav"]

    chapter_index = 0
    chapter_index_parts = 0
    part_count = 0
    for chapter in chapters:
        if chapter["free"]:
            if not chapter["nsfw"] or args.download_nsfw:
                chapter_index += 1
                chapter_index_parts += 1
                print(f"Downloading chapter {chapter_index}: {chapter['title']}")
                downloadChapter(f"https://tapas.io/episode/{chapter['id']}", title, chapter_index)

                book_chapter = epub.EpubHtml(title=chapter["title"], file_name=f"chapter{chapter_index}.xhtml")
                book_chapter.content = '<body style="margin: 0;">'

                imgs = sorted(os.listdir(f"data/{make_safe_filename_windows(title)}/{chapter_index}"), key=getNumericIndex)
                for img in imgs:
                    print(f"\rAdding image {getNumericIndex(img)}/{len(imgs)} to comic", end="")
                    image = epub.EpubItem(file_name=f"chapter{chapter_index}/{img}", content=open(f"data/{make_safe_filename_windows(title)}/{chapter_index}/{img}", "rb").read())
                    book.add_item(image)
                    book_chapter.content += f'<img style="height: 100%;" src="chapter{chapter_index}/{img}"/>'
                print("")

                book_chapter.content += "</body>"

                # Add chapter to the book
                book.add_item(book_chapter)
                book.toc.append(epub.Link(f"chapter{chapter_index}.xhtml", chapter["title"], f"chapter{chapter_index}"))

                book.spine.append(book_chapter)

                print("") # Add empty line at the end of a chapter
                if args.split_into_parts:
                    if chapter_index_parts == args.chapters_per_part:
                        chapter_index_parts = 0
                        part_count += 1

                        # Add default NCX and Nav file
                        book.add_item(epub.EpubNcx())
                        book.add_item(epub.EpubNav())

                        # Save the ePub
                        print(f"Saving comic part {part_count}")
                        epub.write_epub(f"{make_safe_filename_windows(title)} - Part {part_count}.epub", book, {})

                        book = epub.EpubBook()
                        book.set_title(f"{title} - Part {part_count + 1}")
                        book.add_author(authors)
                        book.spine = ["nav"]
                        
                        print("")
            else:
                chapter_index += 1
                print(f"Skipping chapter {chapter_index}: {chapter['title']}. Because it's nsfw")
        else:
            chapter_index += 1
            print(f"Skipping chapter {chapter_index}: {chapter['title']}. Because not free")

            
    if not args.split_into_parts:
        # Add default NCX and Nav file
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        # Save the ePub
        print("Saving comic")
        epub.write_epub(f"{make_safe_filename_windows(title)}.epub", book, {})
    elif chapter_index_parts != 0:
        part_count += 1

        # Add default NCX and Nav file
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        # Save the ePub
        print(f"Saving comic part {part_count}")
        epub.write_epub(f"{make_safe_filename_windows(title)} - Part {part_count}.epub", book, {})

    if args.clean_up:
        print("Cleaning up")
        shutil.rmtree(f"data/{make_safe_filename_windows(title)}")

    print("\n") # Add 2 empty lines at the end of a book

for link in args.link.split(','):
    downloadComic(link)