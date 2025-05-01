import requests
import json

API_KEY = "bd67649cef144456ba8582830e98cdec"

CALORIE_MAP = {
    "low": 2200,
    "moderate": 1800,
    "high": 1500
}

def get_meal_plan(risk_level, preference, time_frame="day"):
    """
    Generate a meal plan (daily or weekly) based on heart disease risk and food preference.
    """
    risk_level = risk_level.lower()
    preference = preference.lower()
    target_calories = CALORIE_MAP.get(risk_level, 2000)

    diet = "lacto-vegetarian" if preference == "veg" else None

    url = "https://api.spoonacular.com/mealplanner/generate"
    params = {
        "timeFrame": time_frame,
        "targetCalories": target_calories,
        "apiKey": API_KEY
    }
    if diet:
        params["diet"] = diet

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json(), target_calories

    except requests.exceptions.RequestException as e:
        print(f"❌ API Request Failed: {e}")
        return None, target_calories

def display_daily_plan(data, risk_level, target_calories, preference):
    print(f"\n🫀 Risk: {risk_level.capitalize()} | 🍴 Preference: {preference.capitalize()} | 🔥 Calories: {target_calories}")
    print("\n🍽️  Daily Meal Plan:\n")

    meal_labels = ["🥣 Breakfast", "🍱 Lunch", "🍽️ Dinner"]
    for label, meal in zip(meal_labels, data.get("meals", [])):
        print(f"{label}: {meal['title']} ({meal['readyInMinutes']} mins)")
        print(f"  ➤ Recipe: {meal['sourceUrl']}")
        print(f"  🖼️ Image: {meal['image']}\n")  # Displaying the image URL
        print()

    nutrients = data.get("nutrients", {})
    if nutrients:
        print("🧪 Nutritional Breakdown:")
        for key, val in nutrients.items():
            print(f"  - {key}: {val:.2f}")
    else:
        print("⚠️ Nutrition info not available.")

def display_weekly_plan(data, risk_level, target_calories, preference):
    print(f"\n🫀 Risk: {risk_level.capitalize()} | 🍴 Preference: {preference.capitalize()} | 🔥 Calories: {target_calories}")
    print("\n📅 Weekly Meal Plan:\n")

    week = data.get("week", {})
    if not week:
        print("⚠️ No weekly data returned.")
        return

    for day, details in week.items():
        print(f"📆 {day.capitalize()}:\n")
        for i, meal in enumerate(details.get("meals", []), start=1):
            print(f"  Meal {i}: {meal['title']} ({meal['readyInMinutes']} mins)")
            print(f"    ➤ Recipe: {meal['sourceUrl']}")
            print(f"    🖼️ Image: {meal['image']}\n")  # Displaying the image URL
        print()
        
def save_plan(data, filename):
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    print(f"\n📁 Meal plan saved to: {filename}")
    

# === Interactive Runner ===
if __name__ == "__main__":
    risk = input("Enter heart risk level (low / moderate / high): ")
    pref = input("Enter food preference (veg / non-veg): ")
    duration = input("Plan type? (day / week): ").strip().lower()

    data, cal = get_meal_plan(risk, pref, time_frame=duration)

    if data:
        if duration == "week":
            display_weekly_plan(data, risk, cal, pref)
            save_plan(data, f"{risk}_{pref}_weekly_plan.json")
        else:
            display_daily_plan(data, risk, cal, pref)
            save_plan(data, f"{risk}_{pref}_daily_plan.json")
