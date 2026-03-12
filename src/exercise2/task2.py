import asyncio
import requests
import os
from urllib.parse import urlparse

class DownloadImg:
    def __init__(self, my_path):
        self.my_path = my_path
        self.success = []
        self.failed = []
        self.tasks = []

    def download(self, url):
        try:
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                raise Exception
            filename = self.get_filename(url)
            file_path = os.path.join(self.my_path, filename)
            with open(file_path, 'wb') as f:
                f.write(response.content)
            self.success.append(url)
        except Exception as e:
            self.failed.append((url, str(e)))

    async def download_task(self, url):  # асинхронная обертка, создаем потоки
        await asyncio.to_thread(self.download, url)
    
    def download_async(self, url):
        task = asyncio.create_task(self.download_task(url))
        self.tasks.append(task)

    #может стат метод????
    def get_filename(self, url):
        parsed = urlparse(url)
        name = os.path.basename(parsed.path)
        if not name or '.' not in name:
            name = f"image_{len(self.success) + len(self.failed) + 1}.jpg"
        return name
    
    def get_pending_count(self):
        return sum(1 for t in self.tasks if not t.done())
    
    async def wait_all(self):
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
    
    def get_results(self):
        return {
            'success': self.success,
            'failed': self.failed,
            'total': len(self.tasks)
        }

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

    print("Введите ссылки на изображения (пустая строка для завершения):")
    while True:
        url = (await asyncio.to_thread(input)).strip()
        if url == "":
            break
        downloader.download_async(url)
    
    if downloader.get_pending_count() > 0:
        print(f"Ожидание {downloader.get_pending_count()} загрузок...")
        await downloader.wait_all()
    
    results = downloader.get_results()
    print(f"Успешно: {len(results['success'])}")
    
if __name__ == "__main__":
    asyncio.run(main())

   #https://images2.pics4learning.com/catalog/s/swamp_15.jpg
    #https://bad-link-no-website-here.strange/img.png
    #https://images2.pics4learning.com/catalog/p/parrot.jpg
