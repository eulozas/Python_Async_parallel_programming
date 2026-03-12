import asyncio
import requests
import os
from urllib.parse import urlparse

class DownloadImg:
    def __init__(self, my_path):
        self.my_path = my_path

    def download(self, url):
          response = requests.get(url)
          filename = self.get_filename(url)
          file_path = os.path.join(self.my_path, filename)
          with open(file_path, 'wb') as f:
            f.write(response.content)
    
    #может стат мемтод????
    def get_filename(self, url):
        parsed = urlparse(url)
        name = os.path.basename(parsed.path)
        if not name:
            name = f"image_1.jpg" #пересмотреть название????
        return name


def get_path():
    path = input("Введите путь для сохранения изображений: ").strip()
    return path


def main():
    path = get_path()
    downloader = DownloadImg(path)
    url = "https://images2.pics4learning.com/catalog/s/swamp_15.jpg"
    downloader.download(url)


if __name__ == "__main__":
    main()
