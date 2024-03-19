from requests_html import HTMLSession
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import colorama
import argparse
import sys

# инициализация модуля colorama
colorama.init()

GREEN = colorama.Fore.GREEN
GRAY = colorama.Fore.LIGHTBLACK_EX
RESET = colorama.Fore.RESET
YELLOW = colorama.Fore.YELLOW

# инициализация множеств ссылок (уникальные ссылки)
ссылки_внутренние = set()
ссылки_внешние = set()

посещенные_ссылки = 0


def is_valid_url(url):
    """
    Проверяет, является ли `url` допустимым URL-адресом.
    """
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)


def извлечь_все_ссылки_с_веб_сайта(url):
    """
    Возвращает все URL-адреса, найденные на `url`, которые принадлежат тому же веб-сайту.
    """
    # все URL-адреса `url`
    ссылки = set()
    # доменное имя URL без протокола
    доменное_имя = urlparse(url).netloc
    # инициализация HTTP-сессии
    сессия = HTMLSession()
    try:
        # совершаем HTTP-запрос и получаем ответ
        ответ = сессия.get(url)
        # выполнение JavaScript
        try:
            ответ.html.render()
        except:
            pass
        soup = BeautifulSoup(ответ.html.html, "html.parser")
        for a_tag in soup.find_all("a"):
            href = a_tag.get("href")
            if href == "" or href is None:
                # пустой тег href
                continue
            # объединяем URL, если это относительная ссылка (не абсолютная ссылка)
            href = urljoin(url, href)
            parsed_href = urlparse(href)
            # удаляем параметры GET URL, фрагменты URL и т. д.
            href = parsed_href.scheme + "://" + parsed_href.netloc + parsed_href.path
            if not is_valid_url(href):
                # не допустимый URL-адрес
                continue
            if href in ссылки_внутренние:
                # уже есть в множестве
                continue
            if доменное_имя not in href:
                # внешняя ссылка
                if href not in ссылки_внешние:
                    print(f"{GRAY}[!] Внешняя ссылка: {href}{RESET}")
                    ссылки_внешние.add(href)
                continue
            print(f"{GREEN}[*] Внутренняя ссылка: {href}{RESET}")
            ссылки.add(href)
            ссылки_внутренние.add(href)
    except Exception as e:
        print(f"{YELLOW}[!] Ошибка при извлечении ссылок с {url}: {e}{RESET}")


def обход_веб_страницы(url, максимальное_количество_ссылок=30):
    """
    Обходит веб-страницу и извлекает все ссылки.
    Вы найдете все ссылки в глобальных переменных множества `ссылки_внешние` и `ссылки_внутренние`.
    параметры:
        максимальное_количество_ссылок (int): максимальное количество URL-адресов для обхода, по умолчанию 30.
    """
    global посещенные_ссылки
    посещенные_ссылки += 1
    print(f"{YELLOW}[*] Обход: {url}{RESET}")
    извлечь_все_ссылки_с_веб_сайта(url)
    if посещенные_ссылки > максимальное_количество_ссылок:
        return
    ссылки = ссылки_внутренние.copy()  # копируем множество ссылок, чтобы не изменять его во время обхода
    for link in ссылки:
        обход_веб_страницы(link, максимальное_количество_ссылок)


def main(url, максимальное_количество_ссылок=30):
    обход_веб_страницы(url, максимальное_количество_ссылок)
    print("[+] Общее количество внутренних ссылок:", len(ссылки_внутренние))
    print("[+] Общее количество внешних ссылок:", len(ссылки_внешние))
    print("[+] Общее количество URL-адресов:", len(ссылки_внешние) + len(ссылки_внутренние))
    print("[+] Общее количество просмотренных URL-адресов:", максимальное_количество_ссылок)

    доменное_имя = urlparse(url).netloc

    # сохраняем внутренние ссылки в файл
    try:
        with open(f"{доменное_имя}_внутренние_ссылки.txt", "w") as f:
            for internal_link in ссылки_внутренние:
                print(internal_link.strip(), file=f)
    except Exception as e:
        print(f"{YELLOW}[!] Ошибка при сохранении внутренних ссылок: {e}{RESET}")

    # сохраняем внешние ссылки в файл
    try:
        with open(f"{доменное_имя}_внешние_ссылки.txt", "w") as f:
            for external_link in ссылки_внешние:
                print(external_link.strip(), file=f)
    except Exception as e:
        print(f"{YELLOW}[!] Ошибка при сохранении внешних ссылок: {e}{RESET}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Инструмент извлечения ссылок с помощью Python")
    parser.add_argument("file", help="Путь к файлу со списком сайтов.")
    parser.add_argument("-m", "--max-urls", help="Максимальное количество URL-адресов для обхода, по умолчанию 30.", default=30, type=int)
    
    args = parser.parse_args()
    file_path = args.file
    максимальное_количество_ссылок = args.max_urls

    try:
        with open(file_path, "r") as file:
            for line in file:
                site_url = line.strip()
                print(f"{YELLOW}[*] Обработка сайта: {site_url}{RESET}")
                ссылки_внутренние.clear()
                ссылки_внешние.clear()
                посещенные_ссылки = 0
                main(site_url, максимальное_количество_ссылок)
                print()  # Добавляем пустую строку между обработанными сайтами
    except FileNotFoundError:
        print(f"{YELLOW}[!] Файл со списком сайтов не найден: {file_path}{RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"{YELLOW}[!] Произошла ошибка при чтении файла: {e}{RESET}")
        sys.exit(1)
