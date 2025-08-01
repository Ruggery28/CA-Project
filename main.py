# main.py
# PROJECT ON GITHUB = https://github.com/Ruggery28/CA-Project
# This program acts as a Nutrition Tracker. It allows a user to:
# 1. Enter a food item.
# 2. Fetch detailed nutritional information for that food item using the Nutritionix API.
# 3. Format the retrieved data into a human-readable string.
# 4. Save the formatted nutritional data to a text file, named with the food item and current date (YYYY-MM-DD).
# 5. Automatically move the saved file into a 'logs' folder.
# 6. Send the nutritional information (both in the email body and as a file attachment) via email.
#
# Prerequisites:
# - Python installed (e.g., Anaconda).
# - Required libraries installed: 'requests' (for API calls).
# - A 'config.py' file in the same directory containing:
#   - NUTRITIONIX_APP_ID and NUTRITIONIX_API_KEY (from Nutritionix developer account)
#   - GMAIL_APP_PASSWORD (a 16-character App Password generated from Google account settings)
#   - SENDER_EMAIL and RECEIVER_EMAIL (Gmail addresses for sending/receiving)
# - For Gmail, 2-Step Verification must be enabled, and an App Password generated.


# --- Import necessary modules ---

import datetime # Used for getting the current date and time for file naming and email subjects.
import os       # Provides functions for interacting with the operating system, like creating directories or moving files.
import requests # A popular library for making HTTP requests (e.g., GET, POST) to web APIs.

import smtplib  # The standard Python library for sending emails using the Simple Mail Transfer Protocol (SMTP).
from email.mime.text import MIMEText         # Used to create the plain text part of an email message.
from email.mime.multipart import MIMEMultipart # Used to create multi-part messages, allowing for both text and attachments.
from email.mime.base import MIMEBase         # A base class for MIME (Multipurpose Internet Mail Extensions) objects, used for attachments.
from email import encoders                   # Used for encoding attachments (e.g., base64) so they can be sent via email.


# --- Configuration Loading ---

# This block attempts to import sensitive API keys and email credentials from 'config.py'.
# Using a separate 'config.py' file (which is also listed in .gitignore) is a security best practice.
# It prevents sensitive information from being accidentally committed to version control systems like Git.
try:
    # Attempt to import all necessary variables from config.py
    from config import (
        NUTRITIONIX_APP_ID,
        NUTRITIONIX_API_KEY,
        GMAIL_APP_PASSWORD,
        SENDER_EMAIL,
        RECEIVER_EMAIL
    )
# If the 'config.py' file is not found, or if any of the required variables are missing,
# an ImportError will be raised.
except ImportError:
    # Print an informative error message to the user.
    print("Error: config.py not found or missing API keys/email details.")
    print("Please create/update config.py with NUTRITIONIX_APP_ID, NUTRITIONIX_API_KEY, GMAIL_APP_PASSWORD, SENDER_EMAIL, RECEIVER_EMAIL.")
    # Exit the program because it cannot function without these crucial configuration details.
    exit()


# --- Function Definitions ---

def get_user_food_input():
    """
    Prompts the user to enter a food item they want to get nutritional information for.
    It includes a basic loop to ensure the user provides a non-empty input.

    Returns:
        str: The food item entered by the user, stripped of leading/trailing whitespace.
    """
    while True:
        food_item = input("Enter a food item to get its nutritional info (e.g., 'apple', 'chicken breast'): ").strip()
        
        # Check if the input is not empty
        if not food_item:
            print("Food item cannot be empty. Please enter something.")
            continue  # Continue the loop to ask again

        # Check if the input consists only of letters and spaces
        if not all(c.isalpha() or c.isspace() for c in food_item):
            print("Invalid input. Please enter a food item using only letters and spaces.")
            continue # Continue the loop to ask again

        # If both checks pass, the input is considered valid
        return food_item

def get_nutritional_info(food_item):
    """
    Fetches nutritional information for a given food item from the Nutritionix API.
    This function handles the HTTP request, includes necessary authentication headers,
    and performs basic error checking for the API response.

    Args:
        food_item (str): The food item to query (e.g., "orange", "1 cup rice").

    Returns:
        dict or None: A Python dictionary containing the raw JSON response from the API if successful,
                      otherwise None if an error occurs or no data is found.
    """
    # The URL for the Nutritionix Natural Language for Nutrients endpoint.
    url = "https://trackapi.nutritionix.com/v2/natural/nutrients"
    
    # Headers required for API authentication and specifying content type.
    # 'x-app-id' and 'x-app-key' are your unique credentials from Nutritionix.
    # 'Content-Type: application/json' tells the API that the request body is JSON.
    headers = {
        "x-app-id": NUTRITIONIX_APP_ID,
        "x-app-key": NUTRITIONIX_API_KEY,
        "Content-Type": "application/json"
    }
    
    # The request body, sent as JSON. Nutritionix expects the food item query under the 'query' key.
    data = {
        "query": food_item
    }

    # Inform the user that an API call is being made.
    print(f"  > Querying Nutritionix API for '{food_item}'...")
    
    try:
        # Make a POST request to the Nutritionix API.
        # 'url': The endpoint.
        # 'headers': Authentication and content type.
        # 'json=data': The request body sent as JSON.
        response = requests.post(url, headers=headers, json=data)
        
        # Check if the HTTP request was successful (status code 200).
        # If not, it raises an HTTPError exception which is caught below.
        response.raise_for_status()
        
        # Parse the JSON response from the API into a Python dictionary.
        response_json = response.json()

        # Check if the 'foods' key exists in the response and if it's not empty.
        # The Nutritionix API returns a list of food items under the 'foods' key.
        if not response_json.get('foods'):
            print(f"  > No detailed nutritional data found for '{food_item}'. Please check spelling or try a more specific item.")
            return None # Return None if no food data is found
        
        return response_json # Return the raw JSON data (as a Python dict)
        
    # --- Error Handling for API Requests ---
    # Catch specific HTTP errors (e.g., 401 Unauthorized, 404 Not Found, 500 Server Error).
    except requests.exceptions.HTTPError as errh:
        print(f"  > HTTP Error occurred: {errh} (Status Code: {errh.response.status_code})")
        if errh.response.status_code == 401:
            print("  > Please double-check your Nutritionix APP_ID and API_KEY in config.py.")
    # Catch errors related to network connection issues (e.g., no internet).
    except requests.exceptions.ConnectionError as errc:
        print(f"  > Connection Error occurred: {errc} (Are you connected to the internet?)")
    # Catch errors if the API takes too long to respond.
    except requests.exceptions.Timeout as errt:
        print(f"  > Timeout Error occurred: {errt} (API took too long to respond)")
    # Catch any other unexpected errors that might occur during the request.
    except requests.exceptions.RequestException as err:
        print(f"  > An unexpected error occurred during the API request: {err}")
    
    return None # Return None if any exception occurred

def format_nutritional_data(raw_data):
    """
    Takes the raw nutritional data (a Python dictionary obtained from the API)
    and formats it into a clean, human-readable string.

    Args:
        raw_data (dict): The dictionary containing nutritional information from the Nutritionix API.

    Returns:
        str: A multi-line string with formatted nutritional details, or a message if no data.
    """
    # Basic check to ensure raw_data is not empty or doesn't contain 'foods' key.
    if not raw_data or not raw_data.get('foods'):
        return "No nutritional data available."

    # Initialize the string with a header.
    formatted_string = "--- Nutritional Information ---\n"
    
    # The Nutritionix API response often contains a list of food items under the 'foods' key.
    # Iterate through each food item found in the response.
    for food in raw_data['foods']:
        # Safely retrieve food attributes using .get() method.
        # .get(key, default_value) returns the value for the key, or default_value if key is not found.
        # .title() capitalizes the first letter of each word in the food name for better presentation.
        food_name = food.get('food_name', 'N/A').title()
        serving_qty = food.get('serving_qty', 1)
        serving_unit = food.get('serving_unit', 'serving')
        
        # Retrieve nutrient values. These can be numbers or None if not available.
        calories = food.get('nf_calories')
        protein = food.get('nf_protein')
        fat = food.get('nf_total_fat')
        carbs = food.get('nf_total_carbohydrate')
        fiber = food.get('nf_dietary_fiber')
        sugar = food.get('nf_sugars')
        sodium = food.get('nf_sodium')

        # Append formatted lines for each nutrient to the string.
        # Use an f-string for easy formatting.
        # Check if the nutrient value is a number (int or float) before formatting to 2 decimal places.
        # If not a number, display "N/A".
        formatted_string += f"\nFood: {food_name} ({serving_qty} {serving_unit})\n"
        formatted_string += f"  Calories: {calories:.2f} kcal\n" if isinstance(calories, (int, float)) else "  Calories: N/A\n"
        formatted_string += f"  Protein: {protein:.2f} g\n" if isinstance(protein, (int, float)) else "  Protein: N/A\n"
        formatted_string += f"  Total Fat: {fat:.2f} g\n" if isinstance(fat, (int, float)) else "  Total Fat: N/A\n"
        formatted_string += f"  Total Carbohydrates: {carbs:.2f} g\n" if isinstance(carbs, (int, float)) else "  Total Carbohydrates: N/A\n"
        formatted_string += f"  Dietary Fiber: {fiber:.2f} g\n" if isinstance(fiber, (int, float)) else "  Dietary Fiber: N/A\n"
        formatted_string += f"  Sugars: {sugar:.2f} g\n" if isinstance(sugar, (int, float)) else "  Sugars: N/A\n"
        formatted_string += f"  Sodium: {sodium:.2f} mg\n" if isinstance(sodium, (int, float)) else "  Sodium: N/A\n"
        formatted_string += "-" * 30 + "\n" # Add a separator for clarity between food items

    return formatted_string # Return the final formatted string

def save_to_file(data, food_item, filename_prefix="nutrition_data"):
    """
    Saves the provided nutritional data string to a text file.
    The filename is constructed to be unique and descriptive, including the food item
    and the current date in YYYY-MM-DD format.

    Args:
        data (str): The formatted nutritional information string to be saved.
        food_item (str): The food item string, used to sanitize and include in the filename.
        filename_prefix (str): An optional prefix for the filename (default is "nutrition_data").

    Returns:
        str or None: The full path to the created file if successful, otherwise None.
    """
    # Get the current date and format it as YYYY-MM-DD.
    current_date = datetime.datetime.now().strftime("%Y-%m-%d") # Changed from %m-%d-%Y to %Y-%m-%d

    # Sanitize the food_item string to ensure it's safe for use in a filename.
    # It removes any characters that are not alphanumeric, spaces, or underscores,
    # then replaces spaces with underscores. This prevents issues with invalid file paths.
    sanitized_food_item = "".join(c for c in food_item if c.isalnum() or c in (' ', '_')).replace(' ', '_')
    
    # Construct the full filename.
    filename = f"{filename_prefix}_{sanitized_food_item}_{current_date}.txt"
    
    try:
        # Open the file in write mode ('w'). If the file doesn't exist, it's created.
        # If it exists, its content is truncated (emptied) before writing.
        with open(filename, 'w') as f:
            f.write(data) # Write the provided data string to the file.
        
        print(f"  > Nutritional data saved temporarily to '{filename}'")
        return filename # Return the path of the newly created file.
    except IOError as e:
        # Catch any Input/Output errors (e.g., permission denied, disk full).
        print(f"  > Error saving file '{filename}': {e}")
        return None # Return None if saving failed.

def send_email(subject, body, to_email, attachment_path=None):
    """
    Sends an email using Gmail's SMTP server. It can include a plain text body
    and an optional file attachment. Authentication is done using an App Password.

    Args:
        subject (str): The subject line of the email.
        body (str): The plain text content of the email.
        to_email (str): The recipient's email address.
        attachment_path (str, optional): The full path to a file to attach. Defaults to None.

    Returns:
        bool: True if the email was sent successfully, False otherwise.
    """
    # Create a MIMEMultipart object. This allows the email to contain both
    # a text part and an attachment part (if provided).
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL      # Set the sender's email address (from config.py)
    msg['To'] = to_email            # Set the recipient's email address
    msg['Subject'] = subject        # Set the subject of the email

    # Attach the main body of the email as plain text.
    msg.attach(MIMEText(body, 'plain'))

    # If an attachment path is provided, try to attach the file.
    if attachment_path:
        try:
            # Open the file in binary read mode ('rb') to read its raw bytes.
            with open(attachment_path, "rb") as attachment:
                # Create a MIMEBase object for the attachment.
                # "application/octet-stream" is a generic content type for binary data.
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read()) # Read the file's content and set it as the payload.
            
            # Encode the payload using Base64 for safe email transmission.
            # This converts binary data into an ASCII string format suitable for emails.
            encoders.encode_base64(part)
            
            # Add a header to specify the filename of the attachment for the recipient.
            # os.path.basename(attachment_path) extracts just the filename from the full path.
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {os.path.basename(attachment_path)}",
            )
            msg.attach(part) # Attach the encoded file part to the email message.
        except Exception as e:
            # Catch any errors that occur during file attachment (e.g., file not found).
            print(f"  > Could not attach file '{attachment_path}': {e}")
            # The function will still try to send the email body, even if the attachment failed.

    # --- Email Sending Logic ---
    try:
        print(f"  > Attempting to send email to {to_email}...")
        # Connect to Gmail's SMTP server securely using SSL encryption on port 465.
        # 'with smtplib.SMTP_SSL(...) as smtp:' ensures the connection is properly closed.
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            # Log in to the SMTP server using the sender's email and the App Password.
            smtp.login(SENDER_EMAIL, GMAIL_APP_PASSWORD)
            # Send the entire email message (including all its parts: text, attachments).
            smtp.send_message(msg)
        print(f"  > Email sent successfully to {to_email}!")
        return True # Return True to indicate successful email sending.
    # --- Email Error Handling ---
    # Catch specific authentication errors (e.g., incorrect App Password).
    except smtplib.SMTPAuthenticationError:
        print("  > Email authentication failed. Check your SENDER_EMAIL and GMAIL_APP_PASSWORD in config.py.")
        print("  > Make sure you are using an App Password for Gmail, not your regular password.")
        return False # Indicate authentication failure.
    # Catch any other general exceptions that might occur during the email sending process.
    except Exception as e:
        print(f"  > Error sending email: {e}")
        return False # Indicate a general sending error.


def main():
    """
    The main function that orchestrates the entire Nutrition Tracker program flow.
    It integrates user input, API calls, data formatting, file saving/moving, and email sending.
    """
    # Print a welcome message for the program.
    print("\n--- Nutrition Tracker (Step 4: Email & File Management) ---")

    # Get the food item from the user using the dedicated function.
    food_item = get_user_food_input()

    # Proceed only if the user entered a food item.
    if food_item:
        # Call the API function to fetch raw nutritional data.
        nutritional_data_raw = get_nutritional_info(food_item)

        # Proceed only if nutritional data was successfully retrieved from the API.
        if nutritional_data_raw:
            # Format the raw data into a readable string.
            formatted_data = format_nutritional_data(nutritional_data_raw)
            # Print the formatted data to the console for immediate user feedback.
            print("\n" + formatted_data)

            # Save the formatted data to a file.
            # The 'save_to_file' function now returns the path to the newly created file.
            original_file_path = save_to_file(formatted_data, food_item)

            # Proceed if the file was successfully saved.
            if original_file_path:
                print(f"  > Processing saved file for '{food_item}'...")

                # --- File Management: Create 'logs' folder and Move File ---
                # Define the name of the directory where files will be moved.
                logs_dir = "logs"
                # Create the 'logs' directory if it doesn't already exist.
                # 'exist_ok=True' prevents an error if the directory is already present.
                os.makedirs(logs_dir, exist_ok=True)

                # Construct the new full path for the file inside the 'logs' directory.
                # os.path.basename() extracts just the filename (e.g., "data_apple_2025-07-30.txt")
                # os.path.join() safely combines the directory and filename for cross-platform compatibility.
                new_file_path = os.path.join(logs_dir, os.path.basename(original_file_path))

                try:
                    # Move the file from its original location to the new 'logs' directory.
                    # os.rename() can move files across directories on the same disk.
                    os.rename(original_file_path, new_file_path)
                    print(f"  > File moved to '{new_file_path}'")
                    # IMPORTANT: Update the 'original_file_path' variable to the new location.
                    # This ensures the 'send_email' function attaches the file from its correct, new path.
                    original_file_path = new_file_path
                except OSError as e:
                    # Handle errors during the file moving process (e.g., permissions, disk issues).
                    print(f"  > Error moving file to logs folder: {e}")
                    print("  > Attempting to send email using the file's original location (if it still exists).")

                # --- Email Preparation and Sending ---
                # Prepare the email subject, ensuring the date format matches the file (YYYY-MM-DD).
                email_subject = f"Nutrition Report for: {food_item} ({datetime.datetime.now().strftime('%Y-%m-%d')})"
                # Prepare the email body, including a friendly message and the formatted nutritional data.
                email_body = f"Hello,\n\nHere is the detailed nutritional information for '{food_item}' that you requested via the Nutrition Tracker program.\n\n{formatted_data}\n\nBest regards,\nYour Nutrition Tracker"

                print("  > Preparing to send email...")
                # Call the 'send_email' function, passing the subject, body, recipient,
                # and the updated path to the saved file as an attachment.
                email_sent_successfully = send_email(email_subject, email_body, RECEIVER_EMAIL, original_file_path)

                # Provide feedback on the email sending operation.
                if email_sent_successfully:
                    print("  > Email operation completed.")
                else:
                    print("  > Email sending failed. Please check the error messages above.")
            else:
                # If file saving failed, inform the user that subsequent operations (email, moving) were skipped.
                print("  > File was not saved, so email and file moving could not be done.")
        else:
            # If API data retrieval failed, inform the user.
            print(f"Could not retrieve nutritional information for '{food_item}'. Operation aborted.")
    else:
        # If no food item was entered, inform the user and exit.
        print("No food item entered. The program will now exit.")


# --- Entry Point of the Program ---

# This standard Python construct ensures that the 'main()' function is called
# only when the script is executed directly (not when it's imported as a module).
if __name__ == "__main__":
    main() # Call the main function to start the program.