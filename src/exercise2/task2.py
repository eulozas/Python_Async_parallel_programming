import asyncio
import requests
import os

class DownloadImg:
    def __init__(self, my_path):
        self.my_path = my_path

    def download(self, url):
          response = requests.get(url)
          filename = "sdfsd.jpg"
          file_path = os.path.join(self.my_path, filename)
          with open(file_path, 'wb') as f:
            f.write(response.content)


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
