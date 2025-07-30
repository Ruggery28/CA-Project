# main.py
import datetime
import os
import requests # Import for making web requests
import json     # Import for working with JSON data
import smtplib  # For connection with email servers (SMTP)
from email.mime.text import MIMEText    # For creating plain text parts of an email
from email.mime.multipart import MIMEMultipart  # For emails with multiple parts (like text + attachment) 
from email.mime.base import MIMEBase    # For handling generic file attachments
from email import encoders  # For encoding attachments for email sending

# Import your API keys and email details from config.py
# This will cause an error if config.py is missing or keys are not defined.
try:
    from config import NUTRITIONIX_APP_ID, NUTRITIONIX_API_KEY, GMAIL_APP_PASSWORD, SENDER_EMAIL, RECEIVER_EMAIL
except ImportError:
    print("Error: config.py not found or missing API keys/email details.")
    # Clarify the error message to include the new email config variables
    print("Please create/update config.py with NUTRITIONIX_APP_ID, NUTRITIONIX_API_KEY, GMAIL_APP_PASSWORD, SENDER_EMAIL, RECEIVER_EMAIL.")
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
    The filename includes the food item (sanitized) and the current date (YYYY-MM-DD).
    Returns the full path to the created file, or None if an error occurs.
    """
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
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

def send_email(subject, body, to_email, attachment_path=None):
    """
    this method will send an email with an optional file using Gmail SMTP.
    Return True if successfully, False othewise.
    """
    #Create the email message container
    msg = MIMEMultipart() # MIMEMultipart allows you to combine text and attachments
    msg['From'] = SENDER_EMAIL # Set the sender email from config.py
    msg['To'] = to_email # Set the recipient email
    msg['Subject'] = subject # Set the email subject

    # Attach the email body (plain text)
    msg.attach(MIMEText(body, 'plain'))

    # Handle file attachment if provided
    if attachment_path:
        try:
            with open(attachment_path, "rb") as attachment: # Open the file in binary read mode ('rb')
                # Create a MIMEBase object for the attachment
                part = MIMEBase("application", "octet-stream") # Generic binary data
                part.set_payload(attachment.read()) # Read the file content into the payload
            encoders.encode_base64(part) # Encode the payload for email transmission (important!)
            part.add_header( # Add headers for the attachment
                "Content-Disposition",
                f"attachment; filename= {os.path.basename(attachment_path)}", # Set the filename for the attachment
            )
            msg.attach(part) # Attach the file part to the message
        except Exception as e:
            print(f"  > Could not attach file '{attachment_path}': {e}")
            # The email body will still try to send even if attachment fails.

    # Send the email via SMTP
    try:
        print(f"  > Attempting to send email to {to_email}...")
        # Connect to Gmail's SMTP server securely using SSL on port 465
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(SENDER_EMAIL, GMAIL_APP_PASSWORD) # Log in using your email and App Password
            smtp.send_message(msg) # Send the entire message object
        print(f"  > Email sent successfully to {to_email}!")
        return True # Indicate success
    except smtplib.SMTPAuthenticationError:
        print("  > Email authentication failed. Check your SENDER_EMAIL and GMAIL_APP_PASSWORD in config.py.")
        print("  > Make sure you are using an App Password for Gmail, not your regular password.")
        return False # Indicate authentication failure
    except Exception as e:
        print(f"  > Error sending email: {e}")
        return False # Indicate other sending errors        

def main():
    """
    Main function to run the Nutrition Tracker program.
    Now includes API call, saving formatted data, sending email,
    and moving/renaming saved files to a 'logs' folder.
    """
    print("\n--- Nutrition Tracker  ---") # Updated welcome message

    food_item = get_user_food_input()

    if food_item:
        nutritional_data_raw = get_nutritional_info(food_item)

        if nutritional_data_raw:
            formatted_data = format_nutritional_data(nutritional_data_raw)
            print("\n" + formatted_data) # Print formatted data to console for immediate feedback

            # Save the formatted data to a file
            # Get the path of the saved file, which now uses YYYY-MM-DD
            original_file_path = save_to_file(formatted_data, food_item)

            if original_file_path: # Only proceed if file was saved successfully
                print(f"  > Processing saved file for item:  '{food_item}'...")

                # 1. Define the 'logs' directory path
                logs_dir = "logs"
                # 2. Create the 'logs' directory if it doesn't exist
                os.makedirs(logs_dir, exist_ok=True) # exist_ok=True means no error if folder exists

                # 3. Construct the new path for the file inside the 'logs' directory
                # os.path.basename extracts just the filename from the original_file_path
                new_file_path = os.path.join(logs_dir, os.path.basename(original_file_path))

                try:
                    # 4. Move (and implicitly rename if target is different) the file
                    # This moves the file from its original location to the 'logs' folder
                    os.rename(original_file_path, new_file_path)
                    print(f"  > File moved to '{new_file_path}'")
                    # Update original_file_path to the new location for email attachment
                    original_file_path = new_file_path
                except OSError as e:
                    print(f"  > Error moving file to logs folder: {e}")
                    # If moving fails, you might decide to stop here or just report the error.
                    # For this assignment, we'll continue with email if the file still exists at the original path.
                    print("  > Attempting to send email using the file's original location (if it still exists).")

                # --- END NEW FILE MANAGEMENT CODE ---

                # Prepare email subject and body
                # Ensure the email subject also uses YYYY-MM-DD for consistency
                email_subject = f"Nutrition Report for: {food_item} ({datetime.datetime.now().strftime('%Y-%m-%d')})"
                email_body = f"Hello,\n\nHere is the detailed nutritional information for '{food_item}' that you requested via the Nutrition Tracker program.\n\n{formatted_data}\n\nBest regards,\nYour Nutrition Tracker"

                print("  > Preparing to send email...")
                # Call the send_email function, passing the (potentially updated) file path as an attachment
                email_sent_successfully = send_email(email_subject, email_body, RECEIVER_EMAIL, original_file_path)

                if email_sent_successfully:
                    print("  > Email operation completed.")
                else:
                    print("  > Email sending failed. Please check the error messages above.")
            else:
                print("  > File was not saved, so email and file moving could not be done.")
        else:
            print(f"Could not retrieve nutritional information for '{food_item}'. Operation aborted.")
    else:
        print("No food item entered. The program will now exit.")

if __name__ == "__main__":
    main()