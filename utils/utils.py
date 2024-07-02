import pandas as pd

from .structs import ProductData
from functools import wraps
from inspect import signature
from collections.abc import Callable

from logger import *


logger = SimpleLogger(
    "main.py",
    datetime_to_str(datetime.now()).split()[0] + ".txt",
    mode="a",
    encoding="utf-8"
)

def debug(info: str, raise_exc: bool = False, **d_kwargs) -> any:
    def debug_wrapper(f: Callable[..., any]) -> any:
        @wraps(f)
        def debug_wrapped(*args, **kwargs) -> any:
            try: return f(*args, **kwargs)
            except Exception as debug_exc:
                sig = signature(f)
                ba = sig.bind(*args, **kwargs)
                log_info = info.format(debug_exc=debug_exc, **d_kwargs, **ba.arguments)
                print(log_info)

                logger.log(LogType.ERROR, f"Method <{f.__name__}> \"{log_info}\"", exc=debug_exc)

                if raise_exc: raise debug_exc

        return debug_wrapped
    
    return debug_wrapper

def get_price(price: str) -> float:
    return float(price) / 100

def get_media_path(url: str) -> str:
    return url.rsplit("/", 1)[0] + "/"

def get_fabric(parts: list[dict[str, any]]) -> dict[str, str]:
    result = {}

    for part in parts:
        name = part.get("description").lower()
        comps = []
        
        if components := part.get("components"):
            for i in components: comps.append(f"{i.get("material")} {i.get("percentage")}")

        if areas := part.get("areas"):
            area_comps = []
            for area in areas:
                area_perc = float(area.get("percentageArea").strip("%")) / 100
                
                for i in area.get("components"):
                    area_comps.append(f"{i.get("material")} {float(i.get("percentage").strip("%")) * area_perc}%")

            comps += area_comps

        result[name] = " ".join(comps)
    return result

def create_df(products: list[ProductData], prefix: str, stocks: bool = False) -> pd.DataFrame:
    if stocks:
        data = {
            "url": [],
            "brand": [],
            "shop_sku": [],
            "newmen_sku": [],
            "in_stock": [],
            "price": []
        }
    else:
        unique_keys = set()
        for i in products: unique_keys.update(i.fabric.keys())
        fabric_fields = { "material_" + key: [] for key in unique_keys }

        data = {
            "url": [],
            "artikul": [],
            "shop_sku": [],
            "newmen_sku": [],
            "bundle_id": [],
            "product_name": [],
            "producer_size": [],
            "price": [],
            "price_before_discount": [],
            "base_type": [],
            "commercial_type": [],
            "brand": [],
            "color": [],
            "manufacturer": [],
            "main_photo": [],
            "additional_photos": [],
            "number": [],
            "vat": [],
            "ozon_id": [],
            "gtin": [],
            "weight_in_pack": [],
            "pack_width": [],
            "pack_length": [],
            "pack_height": [],
            "images_360": [],
            "note": [],
            "keywords": [],
            "in_stock": [],
            "card_num": [],
            "error": [],
            "warning": [],
            "num_packs": [],
            "category": [],
            "content_unit": [],
            "net_quantity_content": [],
            "instruction": [],
            "info_sheet": [],
            "product_description": [],
            "non_food_ingredients_description": [],
            "application_description": [],
            "company_address_description": [],
            "care_label_description": [],
            "country_of_origin_description": [],
            "warning_label_description": [],
            "sustainability_description": [],
            "required_fields_description": [],
            "additional_information_description": [],
            "hazard_warnings_description": [],
            "leaflet_description": [],
            "gender": [],
            "care": []
        } | fabric_fields

    for i in products:
        if stocks:
            data["url"].append(i.url)
            data["brand"].append(i.brand)
            data["shop_sku"].append(i.sku)
            data["newmen_sku"].append(prefix + str(i.season_sku))
            data["in_stock"].append(i.in_stock)
            data["price"].append(i.price)
        else:
            if not i.images: i.images = ["", ""]

            data["url"].append(i.url)
            data["artikul"].append(i.sku)
            data["shop_sku"].append(i.sku)
            data["newmen_sku"].append(prefix + str(i.season_sku))
            data["bundle_id"].append(i.spu)
            data["product_name"].append(i.name)
            data["producer_size"].append(i.size)
            data["price"].append(i.price)
            data["price_before_discount"].append("")
            data["base_type"].append("")
            data["commercial_type"].append("")
            data["brand"].append(i.brand)
            data["color"].append(i.color)
            data["manufacturer"].append("")
            data["main_photo"].append(i.images[0])
            data["additional_photos"].append(",".join(i.images[1:]))
            data["number"].append("")
            data["vat"].append("")
            data["ozon_id"].append("")
            data["gtin"].append("")
            data["weight_in_pack"].append("")
            data["pack_width"].append("")
            data["pack_length"].append("")
            data["pack_height"].append("")
            data["images_360"].append("")
            data["note"].append("")
            data["keywords"].append("")
            data["in_stock"].append(i.in_stock)
            data["card_num"].append("")
            data["error"].append("")
            data["warning"].append("")
            data["num_packs"].append("")
            data["category"].append(i.category)
            data["content_unit"].append("")
            data["net_quantity_content"].append("")
            data["instruction"].append("")
            data["info_sheet"].append("")
            data["product_description"].append(i.description)
            data["non_food_ingredients_description"].append("")
            data["application_description"].append("")
            data["company_address_description"].append("")
            data["care_label_description"].append("")
            data["country_of_origin_description"].append("")
            data["warning_label_description"].append("")
            data["sustainability_description"].append("")
            data["required_fields_description"].append("")
            data["additional_information_description"].append("")
            data["hazard_warnings_description"].append("")
            data["leaflet_description"].append("")
            data["gender"].append(i.gender[0].upper()),
            data["care"].append(",".join(i.care))

            for field in fabric_fields:
                data[field].append(i.fabric.get(field.replace("material_", ""), ""))

    return pd.DataFrame(data)