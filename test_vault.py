from ghost import auth, bungie
import json

# Use stored tokens
tokens = auth.STORED_TOKENS
if not tokens:
    print('No stored tokens')
    exit()

bungie_client = bungie.BungieClient()
bungie_client.authenticate_user(tokens)

# Get membership
membership = bungie_client.get_membership_data_for_current_user()
destiny_membership_id = membership['Response']['destinyMemberships'][0]['membershipId']
destiny_membership_type = membership['Response']['destinyMemberships'][0]['membershipType']

print(f'Membership: {destiny_membership_id}, type: {destiny_membership_type}')

# Get profile with inventory
profile = bungie_client.get_profile(destiny_membership_type, destiny_membership_id, [102])

items = profile['Response']['profileInventory']['data']['items']
print(f'Total items in profileInventory: {len(items)}')

weapons_in_vault = [item for item in items if item.get('location') == 2 and item.get('itemType') == 3]
print(f'Weapons in vault: {len(weapons_in_vault)}')

if weapons_in_vault:
    for item in weapons_in_vault[:5]:
        print(f'Item hash: {item.get("itemHash")}, location: {item.get("location")}, type: {item.get("itemType")}')
else:
    print('No weapons found in vault')

# Also check all locations and types
locations = {}
types = {}
for item in items:
    loc = item.get('location', 'unknown')
    typ = item.get('itemType', 'unknown')
    locations[loc] = locations.get(loc, 0) + 1
    types[typ] = types.get(typ, 0) + 1

print(f'Locations: {locations}')
print(f'Types: {types}')