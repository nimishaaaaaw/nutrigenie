import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from pydantic import Field
from typing import List
from typing import Optional
import pandas as pd
import os
import urllib.request

from model import recommend, output_recommended_recipes

# Download dataset if not already present
DATA_PATH = os.path.join(os.path.dirname(__file__), 'dataset.csv.gz')
DATASET_URL = "https://huggingface.co/datasets/nimishaaaw/nutrigenie-data/resolve/main/dataset.csv.gz"

if not os.path.exists(DATA_PATH):
    print("Downloading dataset from Hugging Face...")
    urllib.request.urlretrieve(DATASET_URL, DATA_PATH)
    print("Dataset download complete.")

dataset = pd.read_csv(DATA_PATH, compression='gzip')

app = FastAPI()


class params(BaseModel):
    n_neighbors: int = 5
    return_distance: bool = False


class PredictionIn(BaseModel):
    nutrition_input: List[float] = Field(min_items=9, max_items=9)
    ingredients: List[str] = []
    params: Optional[params]


class Recipe(BaseModel):
    Name: str
    CookTime: str
    PrepTime: str
    TotalTime: str
    RecipeIngredientParts: List[str]
    Calories: float
    FatContent: float
    SaturatedFatContent: float
    CholesterolContent: float
    SodiumContent: float
    CarbohydrateContent: float
    FiberContent: float
    SugarContent: float
    ProteinContent: float
    RecipeInstructions: List[str]


class PredictionOut(BaseModel):
    output: Optional[List[Recipe]] = None


@app.get("/")
def home():
    return {"health_check": "OK"}


@app.post("/predict/", response_model=PredictionOut)
def update_item(prediction_input: PredictionIn):
    recommendation_dataframe = recommend(
        dataset,
        prediction_input.nutrition_input,
        prediction_input.ingredients,
        prediction_input.params.dict()
    )
    output = output_recommended_recipes(recommendation_dataframe)
    if output is None:
        return {"output": None}
    else:
        return {"output": output}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8080, reload=True)