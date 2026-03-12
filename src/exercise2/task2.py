import asyncio
import requests
import os
from urllib.parse import urlparse

class DownloadImg:
    def __init__(self, my_path):
        self.my_path = my_path
        self.success = []
        self.failed = []
        self.task = []

    def download(self, url):
        try:
            response = requests.get(url)
            if response.status_code != 200:
                raise Exception
            filename = self.get_filename(url)
            file_path = os.path.join(self.my_path, filename)
            with open(file_path, 'wb') as f:
                f.write(response.content)
            self.success.append(url)
        except Exception as e:
            self.failed.append((url, str(e)))

    async def download_async(self, url):  # асинхронная обертка, создаем потоки
        await asyncio.to_thread(self.download, url)

    #может стат метод????
    def get_filename(self, url):
        parsed = urlparse(url)
        name = os.path.basename(parsed.path)
        if not name or '.' not in name:
            name = f"image_{len(self.success) + len(self.failed) + 1}.jpg"
        return name


def get_path():
    while True:
        path = input("Введите путь для сохранения изображений: ").strip()
        try:
            test_file = os.path.join(path, "test.tmp")
            with open(test_file, "wb") as f:
                f.write(b"test")
            os.remove(test_file)
            return path
        except PermissionError:
            print("Нет прав на запись в эту папку")
        except FileNotFoundError:
            print("Путь не существует")


async def main():
    path = get_path()
    downloader = DownloadImg(path)
    tasks = []

    print("Введите ссылки на изображения (пустая строка для завершения):")
    while True:
        url = input().strip()
        if url == "":
            break
        task = asyncio.create_task(downloader.download_async(url))    
        tasks.append(task)
 
    
    await asyncio.gather(*tasks, return_exceptions=True)

if __name__ == "__main__":
    asyncio.run(main())

   #https://images2.pics4learning.com/catalog/s/swamp_15.jpg
    #https://bad-link-no-website-here.strange/img.png
    #https://images2.pics4learning.com/catalog/p/parrot.jpg