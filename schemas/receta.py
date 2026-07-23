from pydantic import BaseModel
from typing import Optional, Any, List
from datetime import datetime
from schemas.ingrediente import IngredienteCreate, IngredienteResponse

class RecetaBase(BaseModel):
    nombre: Optional[str] = None
    descripcion: str
    info_nutri: Optional[Any] = None
    instrucciones: Optional[Any] = None
    consejos: Any  # Modificado a Any para coincidir con el tipo JSON de tu DDL
    id_user: Optional[int] = None
    id_categoria: Optional[int] = None
    foto: Optional[str] = None

class RecetaCreate(RecetaBase):
    pass

class RecetaUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    info_nutri: Optional[Any] = None
    instrucciones: Optional[Any] = None
    consejos: Optional[Any] = None
    id_categoria: Optional[int] = None
    foto: Optional[str] = None

class RecetaResponse(BaseModel):
    id: int
    nombre: Optional[str] = None
    descripcion: str
    info_nutri: Optional[Any] = None
    instrucciones: Optional[Any] = None
    consejos: Optional[Any] = None
    id_user: Optional[int] = None
    id_categoria: Optional[int] = None
    created_at: datetime
    is_deleted: Optional[datetime] = None
    foto: Optional[str] = None
    ingredientes: List[IngredienteResponse] = [] 

    class Config:
        from_attributes = True

#  AGREGA ESTA CLASE AQUÍ CON EL EJEMPLO POR DEFECTO
class PayloadCrearReceta(BaseModel):
    receta: RecetaCreate
    ingredientes: List[IngredienteCreate]

    class Config:
        json_schema_extra = {
            "example": {
                "receta": {
                    "nombre": "Pollo al Curry con Vegetales",
                    "descripcion": "Una receta clásica oriental optimizada para balances calóricos medianos.",
                    "info_nutri": {
                        "calorias": 450,
                        "proteinas": "35g",
                        "carbohidratos": "12g",
                        "grasas": "18g"
                    },
                    "instrucciones": [
                        "Cortar la pechuga en dados medianos.",
                        "Dorar en una sartén con aceite de oliva por 5 minutos.",
                        "Añadir la crema, el curry en polvo y remover a fuego bajo.",
                        "Dejar reducir por 10 minutos y servir caliente."
                    ],
                    "consejos": {
                        "tip_cocina": "Puedes sustituir la crema de leche por leche de coco para una versión más ligera.",
                        "conservacion": "Se mantiene en la nevera hasta por 3 días en envase hermético."
                    },
                    "id_categoria": 1
                },
                "ingredientes": [
                    {
                        "ingrediente": "Pechuga de Pollo",
                        "cantidad": 500,
                        "unidad": "gr"
                    },
                    {
                        "ingrediente": "Curry en Polvo",
                        "cantidad": 2,
                        "unidad": "cucharadas"
                    },
                    {
                        "ingrediente": "Crema de Leche",
                        "cantidad": 200,
                        "unidad": "ml"
                    }
                ]
            }
        }
