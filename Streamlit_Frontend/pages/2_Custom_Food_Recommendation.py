import streamlit as st
import pandas as pd
from Generate_Recommendations import Generator
from ImageFinder.ImageFinder import get_images_links as find_image
from streamlit_echarts import st_echarts

st.set_page_config(page_title="Custom Food Recommendation", page_icon="🔍", layout="wide")

nutritions_values = ['Calories', 'FatContent', 'SaturatedFatContent', 'CholesterolContent',
                     'SodiumContent', 'CarbohydrateContent', 'FiberContent', 'SugarContent', 'ProteinContent']

nutritions_limits = {
    'Calories':            (0, 2000),
    'FatContent':          (0, 100),
    'SaturatedFatContent': (0, 13),
    'CholesterolContent':  (0, 300),
    'SodiumContent':       (0, 2300),
    'CarbohydrateContent': (0, 325),
    'FiberContent':        (0, 50),
    'SugarContent':        (0, 40),
    'ProteinContent':      (0, 40),
}

title = "<h1 style='text-align: center;'>🥘Custom Food Recommendation</h1>"
st.markdown(title, unsafe_allow_html=True)

# ── Nutritional value sliders (all default to 0) ───────────────────────────
st.header("Nutritional values:")
nutritional_values = []
for nutrient in nutritions_values:
    lo, hi = nutritions_limits[nutrient]
    val = st.slider(nutrient, min_value=lo, max_value=hi, value=0)
    nutritional_values.append(val)

# ── Recommendation options ─────────────────────────────────────────────────
st.header("Recommendation options (OPTIONAL):")
nb_recommendations = st.slider("Number of recommendations", min_value=5, max_value=20, value=5, step=1)
ingredients_input = st.text_input(
    'Specify ingredients to include in the recommendations separated by ";" :',
    placeholder="Ingredient1;Ingredient2;..."
)
st.caption("Example: Milk;eggs;butter;chicken...")

generate_btn = st.button("Generate")

# ── Session state ──────────────────────────────────────────────────────────
if 'custom_generated' not in st.session_state:
    st.session_state.custom_generated = False
    st.session_state.custom_recommendations = []

if generate_btn:
    # Parse ingredients string into a list
    ingredients_list = [i.strip() for i in ingredients_input.split(';') if i.strip()] if ingredients_input else []
    params = {'n_neighbors': nb_recommendations, 'return_distance': False}

    with st.spinner("Finding matching recipes..."):
        generator = Generator(
            nutrition_input=nutritional_values,
            ingredients=ingredients_list,
            params=params
        )
        raw = generator.generate()
        print("STATUS:", raw.status_code)
        print("RESPONSE:", raw.text)
        response = raw.json()
        recipes = response.get('output', [])

        if not recipes:
            st.warning("No recipes found. Try adjusting the nutritional values.")
        else:
            for recipe in recipes:
                recipe['image_link'] = find_image(recipe['Name'])
            st.session_state.custom_recommendations = recipes
            st.session_state.custom_generated = True

if st.session_state.custom_generated and st.session_state.custom_recommendations:
    recipes = st.session_state.custom_recommendations

    # ── Recommended recipes expanders ─────────────────────────────────────
    st.subheader("Recommended recipes:")
    num_cols = min(len(recipes), 5)
    cols = st.columns(num_cols)
    for i, recipe in enumerate(recipes):
        with cols[i % num_cols]:
            with st.expander(recipe['Name']):
                recipe_link = recipe['image_link']
                recipe_img = f'<div><center><img src={recipe_link} alt={recipe["Name"]}></center></div>'
                st.markdown(recipe_img, unsafe_allow_html=True)
                nutritions_df = pd.DataFrame({value: [recipe[value]] for value in nutritions_values})
                st.markdown('<h5 style="text-align:center;font-family:sans-serif;">Nutritional Values (g):</h5>', unsafe_allow_html=True)
                st.dataframe(nutritions_df)
                st.markdown('<h5 style="text-align:center;font-family:sans-serif;">Ingredients:</h5>', unsafe_allow_html=True)
                for ingredient in recipe['RecipeIngredientParts']:
                    st.markdown(f"- {ingredient}")
                st.markdown('<h5 style="text-align:center;font-family:sans-serif;">Recipe Instructions:</h5>', unsafe_allow_html=True)
                for instruction in recipe['RecipeInstructions']:
                    st.markdown(f"- {instruction}")
                st.markdown('<h5 style="text-align:center;font-family:sans-serif;">Cooking and Preparation Time:</h5>', unsafe_allow_html=True)
                st.markdown(f"""
- Cook Time       : {recipe['CookTime']}min
- Preparation Time: {recipe['PrepTime']}min
- Total Time      : {recipe['TotalTime']}min
                """)

    # ── Overview section ───────────────────────────────────────────────────
    st.subheader("Overview:")
    recipe_names = [r['Name'] for r in recipes]
    selected_name = st.selectbox("Select a recipe", recipe_names, key="overview_select")
    selected_recipe = next(r for r in recipes if r['Name'] == selected_name)

    st.markdown('<h5 style="text-align:center;">Nutritional Values:</h5>', unsafe_allow_html=True)
    donut_option = {
        "title": {
            "text": "Nutrition values",
            "subtext": selected_name,
            "left": "center"
        },
        "tooltip": {"trigger": "item"},
        "legend": {"orient": "vertical", "left": "left"},
        "series": [{
            "name": "Nutrition",
            "type": "pie",
            "radius": ["40%", "70%"],
            "data": [
                {"value": round(selected_recipe[n], 1), "name": n}
                for n in nutritions_values
            ],
            "emphasis": {
                "itemStyle": {
                    "shadowBlur": 10,
                    "shadowOffsetX": 0,
                    "shadowColor": "rgba(0,0,0,0.5)"
                }
            }
        }]
    }
    st_echarts(options=donut_option, height="500px", key="overview_donut")

st.write("check out this [Recipe link](https://www.food.com/search/)")