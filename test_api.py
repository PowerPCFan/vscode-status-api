import requests
import json
import time
import random
import sqlite3
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:5000"
TEST_USER_ID = "9247395162511234"  # Updated to 16 digits
TEST_USER_ID_RANDOM = str(random.randint(1000000000000000, 9999999999999999))  # 16 digits
TEST_AUTH_TOKEN = "test-token-123456"

# Database configuration (matching the database.py setup)
script_dir = Path(__file__).resolve().parent
DB_FILE = script_dir / "data" / "user_statuses.db"

def verify_database_setup():
    """Verify that the SQLite database is properly set up"""
    print("Verifying SQLite database setup...")
    try:
        if not DB_FILE.exists():
            print("Database file doesn't exist yet - will be created on first use")
            return True
            
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Check if users table exists and has correct schema
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='users'")
        result = cursor.fetchone()
        
        if result:
            print("✓ Users table exists")
            print(f"Schema: {result[0]}")
            
            # Check table structure
            cursor.execute("PRAGMA table_info(users)")
            columns = cursor.fetchall()
            expected_columns = {'user_id', 'auth_token', 'created_at', 'last_updated', 'status_data'}
            actual_columns = {col[1] for col in columns}
            
            if expected_columns.issubset(actual_columns):
                print("✓ Table schema is correct")
                conn.close()
                return True
            else:
                print(f"✗ Missing columns: {expected_columns - actual_columns}")
                conn.close()
                return False
        else:
            print("✗ Users table does not exist")
            conn.close()
            return False
            
    except Exception as e:
        print(f"Error verifying database: {e}")
        return False

def test_update_status():
    """Test the update-status endpoint with non-existent user"""
    print("Testing update-status endpoint (non-existent user)...")
    
    url = f"{BASE_URL}/update-status"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {TEST_AUTH_TOKEN}"
    }
    
    data = {
        "userId": TEST_USER_ID_RANDOM,
        "timestamp": int(time.time() * 1000),
        "activity": "coding",
        "file": "test.py",
        "language": "python",
        "workspace": "test-workspace"
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 404  # Expecting 404 for non-existent user
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_update_status_existing():
    """Test the update-status endpoint with existing user"""
    print("\nTesting update-status endpoint (existing user)...")
    
    url = f"{BASE_URL}/update-status"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {TEST_AUTH_TOKEN}"
    }
    
    data = {
        "userId": TEST_USER_ID,
        "timestamp": int(time.time() * 1000),
        "activity": "debugging",
        "file": "main.py",
        "language": "python",
        "workspace": "test-workspace"
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200  # Expecting 200 for existing user
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_update_status_wrong_token():
    """Test the update-status endpoint with wrong token"""
    print("\nTesting update-status endpoint (wrong token)...")
    
    url = f"{BASE_URL}/update-status"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer wrong-token"
    }
    
    data = {
        "userId": TEST_USER_ID,
        "timestamp": int(time.time() * 1000),
        "activity": "coding",
        "file": "test.py",
        "language": "python",
        "workspace": "test-workspace"
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 401  # Expecting 401 for wrong token
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_register_existing_user():
    """Test registering an existing user"""
    print("\nTesting register-user endpoint (existing user)...")
    
    url = f"{BASE_URL}/register-user"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer different-token"
    }
    
    data = {
        "userId": TEST_USER_ID
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 409  # Expecting 409 for user already exists
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_get_status():
    """Test the get-status endpoint"""
    print("\nTesting get-status endpoint...")
    
    url = f"{BASE_URL}/get-status"
    params = {"userId": TEST_USER_ID}
    
    try:
        response = requests.get(url, params=params)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_get_status_not_found():
    """Test the get-status endpoint with non-existent user"""
    print("\nTesting get-status endpoint with non-existent user...")
    
    url = f"{BASE_URL}/get-status"
    params = {"userId": "9999999999999999"}  # Updated to 16 digits
    
    try:
        response = requests.get(url, params=params)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 404
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    """Run all tests"""
    print("Running VSCode Status Tests with SQLite Database")
    print("=" * 50)
    
    # Verify database setup
    db_ok = verify_database_setup()
    if not db_ok:
        print("Database verification failed. Tests may not work correctly.")
        
    print("\nStarting API tests...")
    print("=" * 40)
    
    # Test update status (new user)
    update_new_success = test_update_status()
    
    # Test update status (existing user)  
    update_existing_success = test_update_status_existing()
    
    # Test update status (wrong token)
    wrong_token_success = test_update_status_wrong_token()
    
    # Test get status
    get_success = test_get_status()
    
    # Test get status not found
    not_found_success = test_get_status_not_found()
    
    # Test register existing user
    register_existing_success = test_register_existing_user()
    
    print("\n" + "=" * 40)
    print("Test Results:")
    print(f"Database Setup: {'PASS' if db_ok else 'FAIL'}")
    print(f"Update Status (New User): {'PASS' if update_new_success else 'FAIL'}")
    print(f"Update Status (Existing User): {'PASS' if update_existing_success else 'FAIL'}")
    print(f"Update Status (Wrong Token): {'PASS' if wrong_token_success else 'FAIL'}")
    print(f"Get Status: {'PASS' if get_success else 'FAIL'}")
    print(f"Get Status Not Found: {'PASS' if not_found_success else 'FAIL'}")
    print(f"Register Existing User: {'PASS' if register_existing_success else 'FAIL'}")
    
    all_tests = [db_ok, update_new_success, update_existing_success, wrong_token_success, 
                 get_success, not_found_success, register_existing_success]
    
    if all(all_tests):
        print("\nAll tests passed! 🎉")
        print("SQLite database is working correctly!")
    else:
        print("\nSome tests failed. 😞")
        if not db_ok:
            print("Note: Database setup failed - this may be the cause of other failures.")
    
    return all(all_tests)

if __name__ == "__main__":
    main()
