# main.py
import datetime
import os
import requests # New import for making web requests
import json     # New import for working with JSON data

# Import your API keys from config.py
# This will cause an error if config.py is missing or keys are not defined.
try:
    from config import NUTRITIONIX_APP_ID, NUTRITIONIX_API_KEY
except ImportError:
    print("Error: config.py not found or missing NUTRITIONIX_APP_ID/API_KEY.")
    print("Please create a config.py file with these variables.")
    exit() # Exit the program if configuration is missing

def get_user_food_input():
    """
    Prompts the user to enter a food item and returns their input.
    Includes basic validation to ensure input is not empty.
    """
    while True:
        food_item = input("Enter a food item to get its nutritional info (e.g., 'apple', 'chicken breast'): ").strip()
        if food_item:
            return food_item
        else:
            print("Food item cannot be empty. Please enter something.")

def get_nutritional_info(food_item):
    """
    Fetches nutritional information for the given food item from Nutritionix API.
    Handles API requests, errors, and returns the raw JSON response.
    """
    url = "https://trackapi.nutritionix.com/v2/natural/nutrients" # The API endpoint
    headers = { # HTTP headers, required by Nutritionix for authentication
        "x-app-id": NUTRITIONIX_APP_ID,
        "x-app-key": NUTRITIONIX_API_KEY,
        "Content-Type": "application/json"
    }
    data = { # The data you send in the request body (the food item query)
        "query": food_item
    }

    print(f"  > Querying Nutritionix API for '{food_item}'...")
    try:
        # This line makes the POST request to the API
        response = requests.post(url, headers=headers, json=data)
        # This checks if the request was successful (status code 200)
        # If not, it raises an exception (e.g., 401 Unauthorized, 404 Not Found)
        response.raise_for_status()
        # If successful, parse the JSON response into a Python dictionary
        response_json = response.json()

        if not response_json.get('foods'):
            print(f"  > No detailed nutritional data found for '{food_item}'. Please check spelling or try a more specific item.")
            return None
        return response_json # Return the raw dictionary for further processing
    # Extensive error handling for different types of request issues
    except requests.exceptions.HTTPError as errh:
        print(f"  > HTTP Error occurred: {errh} (Status Code: {errh.response.status_code})")
        if errh.response.status_code == 401:
            print("  > Please double-check your Nutritionix APP_ID and API_KEY in config.py.")
    except requests.exceptions.ConnectionError as errc:
        print(f"  > Connection Error occurred: {errc} (Are you connected to the internet?)")
    except requests.exceptions.Timeout as errt:
        print(f"  > Timeout Error occurred: {errt} (API took too long to respond)")
    except requests.exceptions.RequestException as err:
        print(f"  > An unexpected error occurred during the API request: {err}")
    return None # Return None if any error occurs

def format_nutritional_data(raw_data):
    """
    Formats the raw JSON data from Nutritionix into a human-readable string.
    """
    if not raw_data or not raw_data.get('foods'):
        return "No nutritional data available."

    formatted_string = "--- Nutritional Information ---\n"
    for food in raw_data['foods']: # Nutritionix response often has a list of 'foods'
        food_name = food.get('food_name', 'N/A').title()
        serving_qty = food.get('serving_qty', 1)
        serving_unit = food.get('serving_unit', 'serving')
        calories = food.get('nf_calories')
        protein = food.get('nf_protein')
        fat = food.get('nf_total_fat')
        carbs = food.get('nf_total_carbohydrate')
        fiber = food.get('nf_dietary_fiber')
        sugar = food.get('nf_sugars')
        sodium = food.get('nf_sodium')

        formatted_string += f"\nFood: {food_name} ({serving_qty} {serving_unit})\n"
        # Use .2f for float formatting, and check if value is numeric before formatting
        formatted_string += f"  Calories: {calories:.2f} kcal\n" if isinstance(calories, (int, float)) else "  Calories: N/A\n"
        formatted_string += f"  Protein: {protein:.2f} g\n" if isinstance(protein, (int, float)) else "  Protein: N/A\n"
        formatted_string += f"  Total Fat: {fat:.2f} g\n" if isinstance(fat, (int, float)) else "  Total Fat: N/A\n"
        formatted_string += f"  Total Carbohydrates: {carbs:.2f} g\n" if isinstance(carbs, (int, float)) else "  Total Carbohydrates: N/A\n"
        formatted_string += f"  Dietary Fiber: {fiber:.2f} g\n" if isinstance(fiber, (int, float)) else "  Dietary Fiber: N/A\n"
        formatted_string += f"  Sugars: {sugar:.2f} g\n" if isinstance(sugar, (int, float)) else "  Sugars: N/A\n"
        formatted_string += f"  Sodium: {sodium:.2f} mg\n" if isinstance(sodium, (int, float)) else "  Sodium: N/A\n"
        formatted_string += "-" * 30 + "\n" # Separator for clarity

    return formatted_string

def save_to_file(data, food_item, filename_prefix="nutrition_data"):
    """
    Saves the provided data to a .txt file.
    The filename includes the food item (sanitized) and the current date (MM-DD-YYYY).
    Returns the full path to the created file, or None if an error occurs.
    """
    current_date = datetime.datetime.now().strftime("%m-%d-%Y")
    # Sanitize food_item for filename to avoid invalid characters
    sanitized_food_item = "".join(c for c in food_item if c.isalnum() or c in (' ', '_')).replace(' ', '_')
    filename = f"{filename_prefix}_{sanitized_food_item}_{current_date}.txt"
    try:
        with open(filename, 'w') as f:
            f.write(data)
        print(f"  > Nutritional data saved to '{filename}'")
        return filename
    except IOError as e:
        print(f"  > Error saving file '{filename}': {e}")
        return None

def main():
    """
    Main function to run the Nutrition Tracker program.
    Now includes API call and saving formatted data.
    """
    print("\nNutrition Tracker")

    food_item = get_user_food_input()

    if food_item:
        nutritional_data_raw = get_nutritional_info(food_item) # CALLING THE API FUNCTION HERE

        if nutritional_data_raw:
            formatted_data = format_nutritional_data(nutritional_data_raw) # FORMATTING THE DATA HERE
            print("\n" + formatted_data) # Print formatted data to console for immediate feedback

            # Save the formatted data to a file
            saved_file_path = save_to_file(formatted_data, food_item)

            if saved_file_path:
                print(f"Success! Data for '{food_item}' fetched and saved.")
            else:
                print(f"Failed to save formatted data for '{food_item}'.")
        else:
            print(f"Could not retrieve nutritional information for '{food_item}'. Please try again.")
    else:
        print("No food item entered. The program will now exit.")


if __name__ == "__main__":
    main()