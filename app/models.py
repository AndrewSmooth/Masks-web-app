from sqlalchemy import ForeignKey, text, Text, String, Sequence
from sqlalchemy.orm import relationship, Mapped, mapped_column

from datetime import date
from typing import Annotated

from database import Base

intpk = Annotated[int, mapped_column(autoincrement=True, primary_key=True)]

class Category(Base):
    __tablename__ = "category_table"

    id: Mapped[intpk]
    name: Mapped[str] = mapped_column(String(45), nullable=False)
    image: Mapped[str] = mapped_column(nullable=False)
    # accessories: Mapped[list["Accessory"]] = relationship(back_populates="category", uselist=True)

    def __str__(self):
        return (f"{self.__class__.__name__}(id={self.id}, "
                f"name={self.name!r},"
                f"image={self.image},")

    def __repr__(self):
        return str(self)

class Accessory(Base):
    __tablename__ = "accessory_table"

    id: Mapped[intpk]
    image: Mapped[str] = mapped_column(nullable=False)
    name: Mapped[str] = mapped_column(String(25), nullable=False)
    category: Mapped["Category"] = relationship()
    category_fk: Mapped[int] = mapped_column(ForeignKey("category_table.id"))

    def __str__(self):
        return (f"{self.__class__.__name__}(id={self.id}, "
                f"name={self.name!r},")

    def __repr__(self):
        return str(self)



    
