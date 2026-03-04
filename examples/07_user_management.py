"""User management: Create users, assign roles, and manage location access.

Usage:
    export SYNUP_API_KEY="your_api_key"
    python 07_user_management.py
"""

import os
from synup import SynupClient, SynupAPIError

api_key = os.environ["SYNUP_API_KEY"]
client = SynupClient(api_key=api_key)

# List current users
users = client.fetch_users()
print(f"Current users ({len(users)}):")
for user in users:
    print(f"  {user.get('email')} — {user.get('firstName')} {user.get('lastName', '')} (role: {user.get('role', {}).get('name', 'N/A')})")

# List available roles
roles = client.fetch_roles()
print(f"\nAvailable roles ({len(roles)}):")
for role in roles:
    print(f"  {role.get('name')} (id: {role.get('id')})")

# Create a new user (uncomment to run)
# role_id = roles[0]["id"]  # Use first role
# result = client.create_user(
#     email="newuser@example.com",
#     role_id=role_id,
#     first_name="New",
#     last_name="User",
# )
# if result.get("success"):
#     print(f"\nCreated user: {result['user']['email']}")
#     user_id = result["user"]["id"]
#
#     # Assign locations to the new user
#     locations = client.fetch_all_locations(first=5)
#     loc_ids = [loc["id"] for loc in locations["locations"]]
#     client.add_user_locations(user_id, loc_ids)
#     print(f"Assigned {len(loc_ids)} locations to user")
# else:
#     print(f"Failed: {result.get('errors')}")
