from pydantic import BaseModel

class CategoryAddDTO(BaseModel):
    name: str

class CategoryDTO(CategoryAddDTO):
    id: int
    image: str
    
class AccessoryAddDTO(BaseModel):
    name: str
    category_fk: int

class AccessoryDTO(AccessoryAddDTO):
    id: int
    image: str

class CategoriesRelDTO(CategoryDTO):
    accessories: list["AccessoryDTO"]

class AccessoryRelDTO(AccessoryDTO):
    category: "CategoriesDTO"


