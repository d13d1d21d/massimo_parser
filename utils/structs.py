from dataclasses import dataclass


@dataclass(eq=False)
class ProductData:
    url: str
    sku: str
    season_sku: str
    spu: str
    name: str               # TRANS
    brand: str  
    category: str           # TRANS
    price: float
    in_stock: int
    color: str              # TRANS
    size: str
    images: list[str]
    description: str        # TRANS
    gender: str
    fabric: dict[str, any]  # TRANS
    care: list[str]         # TRANS

    def __eq__(self, other: any) -> bool:
        if isinstance(other, ProductData):
            return self.sku == other.sku
        
        return False
    
    def __hash__(self) -> int:
        return hash(self.sku)


@dataclass(eq=True, frozen=True)
class Store:
    country: str
    base_url: str
    store_id: str

@dataclass(eq=False, frozen=True)
class Category:
    shop: Store
    name: str
    id: str

    def __eq__(self, other: any) -> bool:
        if isinstance(other, Category):
            return self.id == other.id
        
        return False
    
    def __hash__(self) -> int:
        return hash(self.id)

@dataclass(eq=False, frozen=True)
class ProductPrototype:
    category: Category
    id: str

    def __eq__(self, other: any) -> bool:
        if isinstance(other, ProductPrototype):
            return self.id == other.id
        
        return False
    
    def __hash__(self) -> int:
        return hash(self.id)


DE_STORE = Store("DE", "https://www.massimodutti.com/de/en", "34009454/30359525")
TR_STORE = Store("TR", "https://www.massimodutti.com/tr/en", "34009471/30359503")

BLACKLISTED_CATEGORIES = (
    2165382,   # women perfumes de
    42775353,  # women bags de
    43022094,  # women jewellery de
    42960742,  # women accessories de
    42611676,  # men accessories de
    42889764,  # men perfumes de
    2014004    # men perfumes tr
)