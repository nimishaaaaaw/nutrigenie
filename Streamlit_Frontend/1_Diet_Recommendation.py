import streamlit as st
import pandas as pd
from Generate_Recommendations import Generator
from random import uniform as rnd
from ImageFinder.ImageFinder import get_images_links as find_image
from streamlit_echarts import st_echarts

st.set_page_config(page_title="Nutrigenie: Personalised Diet Recommender", page_icon="🥗", layout="wide")

nutritions_values = ['Calories', 'FatContent', 'SaturatedFatContent', 'CholesterolContent', 'SodiumContent', 'CarbohydrateContent', 'FiberContent', 'SugarContent', 'ProteinContent']

if 'person' not in st.session_state:
    st.session_state.generated = False
    st.session_state.recommendations = None
    st.session_state.person = None
    st.session_state.weight_loss_option = None

class Person:
    def __init__(self, age, height, weight, gender, activity, meals_calories_perc, weight_loss):
        self.age = age
        self.height = height
        self.weight = weight
        self.gender = gender
        self.activity = activity
        self.meals_calories_perc = meals_calories_perc
        self.weight_loss = weight_loss

    def calculate_bmi(self):
        bmi = round(self.weight / ((self.height / 100) ** 2), 2)
        return bmi

    def display_result(self):
        bmi = self.calculate_bmi()
        bmi_string = f'{bmi} kg/m²'
        if bmi < 18.5:
            category = 'Underweight'
            color = 'Red'
        elif 18.5 <= bmi < 25:
            category = 'Normal'
            color = 'Green'
        elif 25 <= bmi < 30:
            category = 'Overweight'
            color = 'Yellow'
        else:
            category = 'Obesity'
            color = 'Red'
        return bmi_string, category, color

    def calculate_bmr(self):
        if self.gender == 'Male':
            bmr = 10 * self.weight + 6.25 * self.height - 5 * self.age + 5
        else:
            bmr = 10 * self.weight + 6.25 * self.height - 5 * self.age - 161
        return bmr

    def calories_calculator(self):
        activites = ['Little/no exercise', 'Light exercise', 'Moderate exercise (3-5 days/wk)', 'Very active (6-7 days/wk)', 'Extra active (very active & physical job)']
        weights = [1.2, 1.375, 1.55, 1.725, 1.9]
        weight = weights[activites.index(self.activity)]
        maintain_calories = self.calculate_bmr() * weight
        return maintain_calories

    def generate_recommendations(self):
        total_calories = self.weight_loss * self.calories_calculator()
        recommendations = []
        for meal in self.meals_calories_perc:
            meal_calories = self.meals_calories_perc[meal] * total_calories
            if meal == 'breakfast':
                recommended_nutrition = [meal_calories, rnd(10, 30), rnd(0, 4), rnd(0, 30), rnd(0, 400), rnd(40, 75), rnd(4, 10), rnd(0, 10), rnd(30, 100)]
            elif meal == 'lunch':
                recommended_nutrition = [meal_calories, rnd(20, 40), rnd(0, 4), rnd(0, 30), rnd(0, 400), rnd(40, 75), rnd(4, 20), rnd(0, 10), rnd(50, 175)]
            elif meal == 'dinner':
                recommended_nutrition = [meal_calories, rnd(20, 40), rnd(0, 4), rnd(0, 30), rnd(0, 400), rnd(40, 75), rnd(4, 20), rnd(0, 10), rnd(50, 175)]
            else:
                recommended_nutrition = [meal_calories, rnd(10, 30), rnd(0, 4), rnd(0, 30), rnd(0, 400), rnd(40, 75), rnd(4, 10), rnd(0, 10), rnd(30, 100)]
            generator = Generator(recommended_nutrition)
            raw = generator.generate()
            print("STATUS:", raw.status_code)
            print("RESPONSE TEXT:", raw.text)
            response = raw.json()
            recommended_recipes = response.get('output', [])
            recommendations.append(recommended_recipes)
        for recommendation in recommendations:
            for recipe in recommendation:
                recipe['image_link'] = find_image(recipe['Name'])
        return recommendations


class Display:
    def __init__(self):
        self.plans = ["Maintain weight", "Mild weight loss", "Weight loss", "Extreme weight loss"]
        self.weights = [1, 0.9, 0.8, 0.6]
        self.losses = ['-0 kg/week', '-0.25 kg/week', '-0.5 kg/week', '-1 kg/week']

    def display_bmi(self, person):
        st.header('BMI CALCULATOR')
        bmi_string, category, color = person.display_result()
        st.metric(label="Body Mass Index (BMI)", value=bmi_string)
        new_title = f'<p style="font-family:sans-serif; color:{color}; font-size: 25px;">{category}</p>'
        st.markdown(new_title, unsafe_allow_html=True)
        st.markdown("Healthy BMI range: 18.5 kg/m² - 25 kg/m².")

    def display_calories(self, person):
        st.header('CALORIES CALCULATOR')
        maintain_calories = person.calories_calculator()
        st.write('The results show a number of daily calorie estimates that can be used as a guideline for how many calories to consume each day to maintain, lose, or gain weight at a chosen rate.')
        for plan, weight, loss, col in zip(self.plans, self.weights, self.losses, st.columns(4)):
            with col:
                st.metric(label=plan, value=f'{round(maintain_calories * weight)} Calories/day', delta=loss, delta_color="inverse")

    def display_recommendation(self, person, recommendations):
        st.header('DIET RECOMMENDATOR')
        with st.spinner('Generating recommendations...'):
            meals = person.meals_calories_perc
            st.subheader('Recommended recipes:')
            for meal_name, column, recommendation in zip(meals, st.columns(len(meals)), recommendations):
                with column:
                    st.markdown(f'##### {meal_name.upper()}')
                    for recipe_idx, recipe in enumerate(recommendation):
                        recipe_name = recipe['Name']
                        unique_key = f"{meal_name}_{recipe_idx}"

                        with st.expander(recipe_name):
                            recipe_link = recipe['image_link']
                            recipe_img = f'<div><center><img src={recipe_link} alt={recipe_name}></center></div>'
                            nutritions_df = pd.DataFrame({value: [recipe[value]] for value in nutritions_values})

                            st.markdown(recipe_img, unsafe_allow_html=True)
                            st.markdown('<h5 style="text-align: center;font-family:sans-serif;">Nutritional Values (g):</h5>', unsafe_allow_html=True)
                            st.dataframe(nutritions_df)

                            # --- DONUT CHART ---
                            
                            donut_option = {
                                "title": {"text": "Macro Split", "left": "center", "textStyle": {"fontSize": 13}},
                                "tooltip": {"trigger": "item"},
                                "legend": {"orient": "vertical", "left": "left"},
                                "series": [{
                                    "name": "Nutrition",
                                    "type": "pie",
                                    "radius": ["40%", "70%"],
                                    "data": [
                                        {"value": round(recipe["CarbohydrateContent"], 1), "name": "Carbs"},
                                        {"value": round(recipe["ProteinContent"], 1), "name": "Protein"},
                                        {"value": round(recipe["FatContent"], 1), "name": "Fat"},
                                        {"value": round(recipe["FiberContent"], 1), "name": "Fiber"},
                                        {"value": round(recipe["SugarContent"], 1), "name": "Sugar"},
                                    ],
                                    "emphasis": {"itemStyle": {"shadowBlur": 10, "shadowOffsetX": 0, "shadowColor": "rgba(0,0,0,0.5)"}}
                                }]
                            }
                            st_echarts(options=donut_option, height="300px", key=f"donut_{unique_key}")

                            # --- BAR CHART ---
                            
                            bar_option = {
                                "title": {"text": "Nutritional Breakdown", "left": "center", "textStyle": {"fontSize": 13}},
                                "tooltip": {"trigger": "axis"},
                                "xAxis": {
                                    "type": "category",
                                    "data": ["Calories", "Fat", "Sat.Fat", "Cholesterol", "Sodium", "Carbs", "Fiber", "Sugar", "Protein"],
                                    "axisLabel": {"rotate": 30, "fontSize": 9}
                                },
                                "yAxis": {"type": "value"},
                                "series": [{
                                    "data": [
                                        round(recipe["Calories"], 1),
                                        round(recipe["FatContent"], 1),
                                        round(recipe["SaturatedFatContent"], 1),
                                        round(recipe["CholesterolContent"], 1),
                                        round(recipe["SodiumContent"], 1),
                                        round(recipe["CarbohydrateContent"], 1),
                                        round(recipe["FiberContent"], 1),
                                        round(recipe["SugarContent"], 1),
                                        round(recipe["ProteinContent"], 1),
                                    ],
                                    "type": "bar",
                                    "itemStyle": {"color": "#5470C6"},
                                    "label": {"show": True, "position": "top", "fontSize": 8}
                                }]
                            }
                            st_echarts(options=bar_option, height="300px", key=f"bar_{unique_key}")

                            st.markdown('<h5 style="text-align: center;font-family:sans-serif;">Ingredients:</h5>', unsafe_allow_html=True)
                            for ingredient in recipe['RecipeIngredientParts']:
                                st.markdown(f"- {ingredient}")
                            st.markdown('<h5 style="text-align: center;font-family:sans-serif;">Recipe Instructions:</h5>', unsafe_allow_html=True)
                            for instruction in recipe['RecipeInstructions']:
                                st.markdown(f"- {instruction}")
                            st.markdown('<h5 style="text-align: center;font-family:sans-serif;">Cooking and Preparation Time:</h5>', unsafe_allow_html=True)
                            st.markdown(f"""
- Cook Time       : {recipe['CookTime']}min
- Preparation Time: {recipe['PrepTime']}min
- Total Time      : {recipe['TotalTime']}min
                            """)

    def display_meal_composition(self, person, recommendations):
        st.subheader('Choose your meal composition:')
        meals = person.meals_calories_perc
        meal_names = list(meals.keys())
        maintain_calories = person.calories_calculator()

        selected_recipes = {}
        cols = st.columns(len(meal_names))
        for meal_name, col, recommendation in zip(meal_names, cols, recommendations):
            with col:
                recipe_names = [r['Name'] for r in recommendation]
                selected = st.selectbox(f'Choose your {meal_name}:', recipe_names, key=f"select_{meal_name}")
                selected_recipes[meal_name] = next(r for r in recommendation if r['Name'] == selected)

        # Total calories chosen
        total_chosen_calories = sum(r['Calories'] for r in selected_recipes.values())

        # --- Red vs Blue Bar Chart: Total Calories chosen vs Maintain weight Calories ---
        st.markdown('<h5 style="text-align: center;">Total Calories in Recipes vs Maintain weight Calories:</h5>', unsafe_allow_html=True)
        calories_bar = {
            "tooltip": {"trigger": "axis"},
            "xAxis": {
                "type": "category",
                "data": ["Total Calories you chose", "Maintain weight Calories"],
                "axisLabel": {"fontSize": 12}
            },
            "yAxis": {"type": "value"},
            "series": [{
                "data": [
                    {"value": round(total_chosen_calories, 1), "itemStyle": {"color": "#e63946"}},
                    {"value": round(maintain_calories, 1), "itemStyle": {"color": "#1d3557"}},
                ],
                "type": "bar",
                "label": {"show": True, "position": "top", "fontSize": 11}
            }]
        }
        st_echarts(options=calories_bar, height="400px", key="calories_comparison_bar")

        # --- Combined Nutritional Donut Chart ---
        st.markdown('<h5 style="text-align: center;">Nutritional Values:</h5>', unsafe_allow_html=True)
        combined = {n: sum(r[n] for r in selected_recipes.values()) for n in nutritions_values}
        donut_combined = {
            "tooltip": {"trigger": "item"},
            "legend": {"orient": "horizontal", "top": "top"},
            "series": [{
                "name": "Nutrition",
                "type": "pie",
                "radius": ["40%", "70%"],
                "data": [{"value": round(combined[n], 1), "name": n} for n in nutritions_values],
                "emphasis": {"itemStyle": {"shadowBlur": 10, "shadowOffsetX": 0, "shadowColor": "rgba(0,0,0,0.5)"}}
            }]
        }
        st_echarts(options=donut_combined, height="450px", key="combined_nutrition_donut")


display = Display()
title = "<h1 style='text-align: center;'>🥗 Nutrigenie: Personalised Diet Recommender</h1>"
st.markdown(title, unsafe_allow_html=True)

with st.form("recommendation_form"):
    st.write("Modify the values and click the Generate button to use")
    age = st.number_input('Age', min_value=2, max_value=120, step=1)
    height = st.number_input('Height(cm)', min_value=50, max_value=300, step=1)
    weight = st.number_input('Weight(kg)', min_value=10, max_value=300, step=1)
    gender = st.radio('Gender', ('Male', 'Female'))
    activity = st.select_slider('Activity', options=['Little/no exercise', 'Light exercise', 'Moderate exercise (3-5 days/wk)', 'Very active (6-7 days/wk)', 'Extra active (very active & physical job)'])
    option = st.selectbox('Choose your weight loss plan:', display.plans)
    st.session_state.weight_loss_option = option
    weight_loss = display.weights[display.plans.index(option)]
    number_of_meals = st.slider('Meals per day', min_value=3, max_value=5, step=1, value=3)
    if number_of_meals == 3:
        meals_calories_perc = {'breakfast': 0.35, 'lunch': 0.40, 'dinner': 0.25}
    elif number_of_meals == 4:
        meals_calories_perc = {'breakfast': 0.30, 'morning snack': 0.05, 'lunch': 0.40, 'dinner': 0.25}
    else:
        meals_calories_perc = {'breakfast': 0.30, 'morning snack': 0.05, 'lunch': 0.40, 'afternoon snack': 0.05, 'dinner': 0.20}
    generated = st.form_submit_button("Generate")

if generated:
    st.session_state.generated = True
    person = Person(age, height, weight, gender, activity, meals_calories_perc, weight_loss)
    print(person)
    with st.container():
        display.display_bmi(person)
    with st.container():
        display.display_calories(person)
    with st.spinner('Generating recommendations...'):
        recommendations = person.generate_recommendations()
        st.session_state.recommendations = recommendations
        st.session_state.person = person

if st.session_state.generated:
    with st.container():
        display.display_recommendation(st.session_state.person, st.session_state.recommendations)
        st.success('Recommendation Generated Successfully !', icon="✅")
    with st.container():
        display.display_meal_composition(st.session_state.person, st.session_state.recommendations)

st.write("check out this [Recipe link](https://www.food.com/search/)")


