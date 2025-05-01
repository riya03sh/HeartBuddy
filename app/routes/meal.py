from flask import Blueprint, render_template, session, request
from utils.meal_planner import get_meal_plan

meal_bp = Blueprint("meal", __name__)

@meal_bp.route("/meal-planner")
def meal_planner():
    risk = session.get("risk_level", "moderate")
    preference = session.get("preference", "non-veg")
    time_frame = request.args.get("duration", "day")
    
    data, target_cal = get_meal_plan(risk, preference, time_frame)
    return render_template("meal_planner/meal_plan.html", data=data, calories=target_cal, risk=risk, preference=preference)
