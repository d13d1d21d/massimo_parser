import concurrent.futures
import platform
import sys
import time

from ordered_set import OrderedSet
from utils.utils import *
from utils.csv_translator import *
from colorama import Fore, Style, just_fix_windows_console
from proxy_client import *
from webparser import *

PREFIX = "MSM-"
insert_headers = [True, True]

if platform.system() == "Windows":
    just_fix_windows_console()


def stop_script() -> None:
    print(f"[{Fore.RED + Style.BRIGHT}X{Style.RESET_ALL}] Не указан магазин для парсинга\nЗапуск: {Style.BRIGHT}python main.py <tr | de>{Style.RESET_ALL}")
    time.sleep(5)
    sys.exit()

if len(sys.argv) > 1:
    match sys.argv[1]:
        case "de":
            shop = DE_STORE
            file_prefix = "de-"
        case "tr":
            shop = TR_STORE
            file_prefix = "tr-"
        case _:
            stop_script()
else:
    stop_script()


translator = CSVTranslator(f"output/{file_prefix}massimodutti-products.csv")
executor = concurrent.futures.ThreadPoolExecutor(50)

proxy_client = ProxyClient(
    map_proxies("http", open("proxy_list.txt").read().split("\n")),
    retries=5
)
parser = Parser(proxy_client)
logger.log_new_run()

n_cat = 0

print(f"[{Fore.CYAN + Style.BRIGHT}⧖{Style.RESET_ALL}] Получение категорий...")
categories = list(filter(lambda x: x.id not in BLACKLISTED_CATEGORIES, parser.get_categories(shop)))

logger.log(LogType.INFO, f"Получено {len(set(categories))} категорий")
print(f"[{Fore.GREEN + Style.BRIGHT}✓{Style.RESET_ALL}] Получено {len(categories)} категорий")

parsed_products = OrderedSet()
cached_skus = set()

for category in categories:
    n_cat += 1

    print(f"\n[{Fore.CYAN + Style.BRIGHT}{n_cat}/{len(categories)}{Style.RESET_ALL}] Получение товаров для {category.name} ({category.id} {category.shop.country})...")
    product_ids = parser.get_products(category)
    logger.log(LogType.INFO, f"Получено {len(product_ids)} товаров из {category.name} ({category.id} {category.shop.country})")
    print(f"[{Fore.GREEN + Style.BRIGHT}✓{Style.RESET_ALL}] Получено {len(product_ids)} товаров. Обработка...")

    for variations in executor.map(parser.get_product_data, product_ids):
        parsed_products.update(
            list(filter(lambda x: x.sku not in cached_skus, variations))
        )
        cached_skus.update(list(i.sku for i in variations))

    print(f"[{Fore.GREEN + Style.BRIGHT}✓{Style.RESET_ALL}] Обработано {len(parsed_products)} вариаций")

if parsed_products:
    create_df(parsed_products, PREFIX, False).to_csv(
        f"output/{file_prefix}massimodutti-products.csv",
        sep=";",
        index=False,
        encoding="utf-8",
        header=insert_headers[0], 
        mode="w" if insert_headers[0] else "a"
    )
    if insert_headers[0]: insert_headers[0] = False
    
    create_df(parsed_products, PREFIX, True).to_csv(
        f"output/{file_prefix}massimodutti.csv",
        sep=";",
        index=False,
        encoding="utf-8",
        header=insert_headers[1], 
        mode="w" if insert_headers[1] else "a"
    )
    if insert_headers[1]: insert_headers[1] = False

    print(f"\n[{Fore.GREEN + Style.BRIGHT}✓{Style.RESET_ALL}] Отчёты сформированы. Перевод файла...")
    logger.log(LogType.INFO, f"Записан чанк из {len(parsed_products)} линий")

    translator.add_new_columns(f"output/{file_prefix}massimodutti-products.temp")
    translated_rows = 0

    for i in translator.translate_rows():
        new_1000 = i // 1000
        if new_1000 > translated_rows:
            translated_rows = new_1000
            print(f"Переведено {i} строк")

    os.remove(f"output/{file_prefix}massimodutti-products.temp")
    os.rename(f"output/{file_prefix}massimodutti-products.csv")
else:
    logger.log(LogType.INFO, f"Товары из {category.name} ({category.id} {category.shop.country}) не найдены")
    print(f"[{Fore.RED + Style.BRIGHT}X{Style.RESET_ALL}] Товары не найдены")

