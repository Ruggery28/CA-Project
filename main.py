#main.py
import datetime
import os

#input to store the food item
def get_user_food_input():
    food_item = input("Enter a food item to get its nutrients info: ")
    return food_item

def save_to_file(data, filename_prefix="nutrition_data"):
    current_data = datetime.datetime.now().strftime("%m-%d-%Y")
    filename = f"{filename_prefix}_{current_data}.txt"
    try:
        with open(filename, 'w') as file:
            file.write(data)
        print(f"Data saved to {filename}")
        return filename # Return the full path to the saved file
    except IOError as e:
        print(f"Error saving file: {e}")
        return None
    
def main():
    print("___ Nutrition Tracker ___")
    food_item = get_user_food_input()
    if food_item:
        data_to_save = f"User entered: {food_item}\n"
        data_to_save += f"Query Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        saved_file = save_to_file(data_to_save)
        if saved_file:
            print(f"Placeholder data for '{food_item}' saved.")
    else:
        print("No food item entered. Exiting.")    




if __name__ == "__main__":
    main()