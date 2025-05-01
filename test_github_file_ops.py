from src.billy import create_file_with_test, update_file_with_test, delete_file_with_commit

# Test creating a file
create_result = create_file_with_test("test_file.txt", "This is a test file created by Billy.", "Test creation by Billy")
print("Create Result:", create_result)

# Test updating the file
update_result = update_file_with_test("test_file.txt", "This is an updated test file by Billy.", "Test update by Billy")
print("Update Result:", update_result)

# Test deleting the file
delete_result = delete_file_with_commit("test_file.txt", "Test deletion by Billy")
print("Delete Result:", delete_result)