from proxy_client import ProxyClient
from utils.structs import *
from utils.utils import *


class Parser:
    BASE = "https://www.massimodutti.com/itxrest"

    def __init__(self, proxy_client: ProxyClient) -> None:
        self.proxy_client = proxy_client

    @debug("Ошибка в получении категорий для {shop.store_id} {shop.country}. Данные об ошибке занесены в логи", True)
    def get_categories(self, shop: Store) -> list[Category]:
        categories = self.proxy_client.retry("GET", self.BASE + f"/2/catalog/store/{shop.store_id}/category?languageId=-1&typeCatalog=1&appId=1").json().get("categories")
        women_collection = next((i for i in categories[0].get("subcategories") if "COLLECTION" in i.get("nameEn")), None).get("subcategories")
        men_collection = next((i for i in categories[1].get("subcategories") if "COLLECTION" in i.get("nameEn")), None).get("subcategories")
        
        women_categories = list(Category(shop, "women " + i.get("nameEn").lower(), i.get("id")) for i in women_collection if i.get("categoryUrl"))
        men_categories = list(Category(shop, "men " + i.get("nameEn").lower(), i.get("id")) for i in men_collection if i.get("categoryUrl"))

        return women_categories + men_categories
    
    @debug("Ошибка в получении списка товаров для {category.name} ({category.id} {category.shop.country}). Данные занесены об ошибке в логи", True)
    def get_products(self, category: Category) -> list[ProductPrototype]:
        resp = self.proxy_client.retry(
            "GET",
            self.BASE + f"/3/catalog/store/{category.shop.store_id}/category/{category.id}/product?languageId=-1&typeCatalog=1&appId=1"
        ).json()

        return list(
            ProductPrototype(
                category,
                i
            )
            for i in resp.get("sortedProductIdsByPricesAsc", [])
        )
    
    @debug("Ошибка в парсинге товара {product.id}. Данные об ошибке занесены в логи")
    def get_product_data(self, product: ProductPrototype) -> ProductData:
        v = []
        if (data := self.proxy_client.retry(
            "GET",
            self.BASE + f"/2/catalog/store/{product.category.shop.store_id}/category/0/product/{product.id}/detail?languageId=-1&appId=1"
        ).json()) and data.get("isBuyable"):
            name = data.get("name")
            brand = "Massimo Dutti"
            description = ". ".join(list(i.get("value") for i in data.get("attributes") if i.get("type") == "DESCRIPTION" and i.get("value")))
            category = product.category.name + " / ".join(filter(bool, [data.get("familyNameEN", "").lower(), data.get("subFamilyNameEN", "").lower()]))
            gender = product.category.name.split(" ")[0]

            if product_summary := data.get("bundleProductSummaries"): product_summary = product_summary[0].get("detail")
            else: product_summary = data.get("detail")
            
            spu = product_summary.get("displayReference")
            care = list(i.get("description").lower() for i in product_summary.get("care"))

            for color in product_summary.get("colors"):
                parsed_sizes = []
                color_id = color.get("id")
                color_name = color.get("name").lower()
                url = product.category.shop.base_url + f"/{data.get("productUrl")}?colorId={color_id}"
                
                fabric = {}
                if composition := color.get("compositionDetail"):
                    fabric = get_fabric(composition.get("parts"))
                
                images = []
                if xmedia := next((i for i in product_summary.get("xmedia", []) if i.get("colorCode") == color_id), None):
                    media_path = "https://static.massimodutti.net/3/photos" + get_media_path(color.get("image").get("url"))
                    images = list(
                        media_path + f"{i}16.jpg"
                        for i in next((i for i in xmedia.get("xmediaLocations") if i.get("set") == 0)).get("locations")[1].get("mediaLocations")
                    )

                    for size in color.get("sizes"):
                        size_name = size.get("name")

                        if size_name not in parsed_sizes and (price := get_price(size.get("price"))) >= 30:
                            parsed_sizes.append(size_name)

                            ref = product_summary.get("reference").split("-")
                            sku = ref[0] + color_id + size_name
                            season_sku = sku + f"-{ref[1]}"
                            in_stock = 2 if any((i.get("visibilityValue") == "SHOW" for i in color.get("sizes") if i.get("name") == size_name)) else 0
                            
                            v.append(
                                ProductData(
                                    url,
                                    sku,
                                    season_sku,
                                    spu + f"-{ref[1]}",
                                    name,
                                    brand,
                                    category,
                                    price,
                                    in_stock,
                                    color_name,
                                    size_name,
                                    images,
                                    description,
                                    gender,
                                    fabric,
                                    care
                                )
                            )
        return v