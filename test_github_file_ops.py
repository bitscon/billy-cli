import logging
import requests

# Configure logging
logging.basicConfig(level=logging.DEBUG, filename="test.log", format="%(asctime)s %(levelname)s:%(message)s")

def simulate_user_request(prompt):
    """Simulate a user request to the Flask app and return the response."""
    url = "http://192.168.1.112:5000/"
    data = {"prompt": prompt}
    try:
        response = requests.post(url, data=data)
        if response.status_code == 200:
            logging.info(f"Request '{prompt}' successful: {response.text[:100]}...")
            return response.text
        else:
            logging.error(f"Request '{prompt}' failed: {response.status_code} - {response.text}")
            return f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        logging.error(f"Request '{prompt}' failed: {str(e)}")
        return f"Error: {str(e)}"

# Test creating a file
create_result = simulate_user_request("Create a file named test_file.txt with content: This is a test file created by Billy")
print("Create Result:", create_result)

# Test updating the file
update_result = simulate_user_request("Update test_file.txt with content: This is an updated test file by Billy")
print("Update Result:", update_result)

# Test deleting the file
delete_result = simulate_user_request("Delete the file test_file.txt")
print("Delete Result:", delete_result)