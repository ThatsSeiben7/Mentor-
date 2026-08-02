import json
import os

PROFILE_FILE = "learner_profile.json"

def load_profile():
    """Loads the user's historical performance. Creates a default if none exists."""
    if not os.path.exists(PROFILE_FILE):
        return {"tier_1_solves": 0, "tier_2_solves": 0, "tier_3_solves": 0}
   
    with open(PROFILE_FILE, "r") as f:
        return json.load(f)

def save_profile(profile):
    """Saves the updated profile to disk."""
    with open(PROFILE_FILE, "w") as f:
        json.dump(profile, f, indent=4)

def update_stats(tier_solved_at):
    """Updates the profile based on which tier the user stopped at."""
    profile = load_profile()
   
    if tier_solved_at == 1:
        profile["tier_1_solves"] += 1
    elif tier_solved_at == 2:
        profile["tier_2_solves"] += 1
    elif tier_solved_at == 3:
        profile["tier_3_solves"] += 1
       
    save_profile(profile)

def calculate_user_level():
    """Evaluates the learner's skill based on historical reliance on hints."""
    profile = load_profile()
    total_bugs = sum(profile.values())
   
    if total_bugs < 3:
        return "assessing" # not enough data yet
       
    if profile["tier_1_solves"] / total_bugs >= 0.5:
        return "advanced"
       
    elif profile["tier_3_solves"] / total_bugs >= 0.5:
        return "beginner"
       
    else:
        return "intermediate"
