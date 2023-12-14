# tapas to .epub converter
A program to download a whole tapas comic into a `.epub` file. (For use with an e-reader or similar.)<br>
Note: **!!This could break at any time because it relies on the current layout of tapas's website!!**

## Installation
Using a venv:
```sh
git clone https://github.com/westhecool/tapas-to-epub.git
cd tapas-to-epub
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

## Usage
```sh
./venv/bin/python3 main.py [link to chapter list of tapas series]
```
The input **must** be a link to the chapter list of the tapas series. Please do not use the mobile version of the site as it's not tested.

## Splitting A Comic Into Parts
You can use the option `--split-into-parts` (Not enabled by default.) to split the comic into multiple files. By default, it splits every 100 chapters into a different file. You can adjust it with the argument `--chapters-per-part N`.

## Tip: Converting to MOBI (Kindle e-reader supported format)
You can use the program [ebook-convert](https://command-not-found.com/ebook-convert) (Which is part of Calibre) to easily convert to `.mobi`:
```sh
ebook-convert input.epub output.mobi
```
