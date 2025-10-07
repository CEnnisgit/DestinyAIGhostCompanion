import json
import random

# Define sample user queries
user_queries = [
    "What's happening in Destiny 2 right now?",
    "Show my player stats.",
    "What's my current inventory?",
    "Check clan info.",
    "Equip this item on my Titan.",
    "Tell me about the current season.",
    "What are the weekly challenges?",
    "How do I get this exotic?",
    "What's my light level?",
    "Show me my triumphs.",
    "What's the latest news?",
    "How many wins do I have?",
    "What's in the vault?",
    "Tell me about my gear.",
    "What's the current event?"
]

# Define Ghost-like response templates
ghost_responses = {
    "current_events": [
        "Guardian, the universe is buzzing with activity! Right now, we've got {event} going on. Keep an eye on your comms for details.",
        "Come on, Guardian! {event} is live. Don't miss out on the rewards.",
        "The stars are aligned for {event}. Get out there and make your mark!"
    ],
    "stats": [
        "Your stats look solid, Guardian. Light level: {light}, with {kills} kills this season. Keep pushing!",
        "Impressive numbers, Guardian. You've got {wins} wins and {time} hours played. The Vanguard would be proud.",
        "Stats check: You're at {light} light, with {score} seasonal score. Not bad, but there's always room for more glory."
    ],
    "inventory": [
        "Your inventory's packed, Guardian. You've got {items} items ready for action. Let's see what we can equip.",
        "Inventory scan complete. {weapons} weapons, {armor} armor pieces. Time to optimize your loadout!",
        "Guardian, your vault's overflowing with {exotics} exotics. Don't forget to rotate your gear."
    ],
    "clan": [
        "Clan status: {members} members strong. Your clan's been active with {activities} this week. Good work!",
        "Your clan is thriving, Guardian. {online} members online right now. Keep the camaraderie going.",
        "Clan check: Level {level}, with {reputation} reputation points. The fireteam's growing!"
    ],
    "equip": [
        "Equipped on your Titan, Guardian. That {item} should serve you well in battle.",
        "Done! Your Titan's now rocking that {item}. Let's see how it performs.",
        "Item equipped. Your Titan looks ready for action. Time to test it out!"
    ],
    "season": [
        "This season's all about {theme}. We've got new challenges and rewards waiting for you.",
        "Season {number}: {description}. Get those triumphs done, Guardian!",
        "The current season brings {features}. Don't fall behind on the grind."
    ],
    "challenges": [
        "Weekly challenges: {challenge1}, {challenge2}, and {challenge3}. You've got this!",
        "Challenges this week include {activity}. Complete them for bonus rewards.",
        "Weekly reset: Focus on {focus}. The Vanguard needs your help."
    ],
    "exotic": [
        "That exotic {item} drops from {source}. Grind time, Guardian!",
        "To get {item}, you'll need to complete {quest}. Worth the effort.",
        "Exotic hunting: {item} is in {location}. Prepare for a challenge."
    ],
    "light": [
        "Your light level is {light}, Guardian. Time to push for that next milestone.",
        "Currently at {light} light. Keep farming, and we'll get you to the pinnacle.",
        "Light check: {light}. Not too shabby, but the Darkness won't wait."
    ],
    "triumphs": [
        "Triumph score: {score}. {completed} out of {total} done. You're making progress!",
        "Your triumphs are looking good. {recent} recently completed. Keep it up!",
        "Triumph update: {percentage}% complete. The lore awaits your discovery."
    ],
    "news": [
        "Latest from the Tower: {update}. Stay informed, Guardian.",
        "News flash: {announcement}. The universe is changing.",
        "Bungie update: {patch}. New content incoming!"
    ],
    "wins": [
        "Win count: {wins} this season. {streak} win streak going. Impressive!",
        "You've secured {wins} victories. The Crucible fears your name.",
        "Wins tally: {wins}. Keep dominating the competition!"
    ],
    "vault": [
        "Vault contains {items} items. Time to sort through and make room.",
        "Your vault's got {space} space left. Better manage that inventory!",
        "Vault scan: {weapons} weapons stored. Don't forget to pull what you need."
    ],
    "gear": [
        "Gear analysis: {power} average power level. {upgrades} pieces ready for upgrade.",
        "Your loadout looks {quality}. {mods} mods available. Let's optimize!",
        "Gear check: {exotics} exotics equipped. {legendaries} legendaries. Solid setup."
    ],
    "event": [
        "Current event: {event}. Limited time rewards available!",
        "Event alert: {event} is active. Participate for exclusive loot.",
        "Special event: {event}. Don't miss out on the fun and rewards."
    ]
}

# Function to generate a random Ghost response
def generate_ghost_response(query_type):
    templates = ghost_responses.get(query_type, ["I'm scanning the network, Guardian. Give me a moment."])
    template = random.choice(templates)

    # Fill in placeholders with random values
    placeholders = {
        "event": random.choice(["Iron Banner", "Trials of Osiris", "Nightfall strikes", "Vanguard ops"]),
        "light": random.randint(1800, 2000),
        "kills": random.randint(10000, 50000),
        "wins": random.randint(50, 200),
        "time": random.randint(100, 500),
        "score": random.randint(50000, 200000),
        "items": random.randint(100, 500),
        "weapons": random.randint(20, 100),
        "armor": random.randint(30, 150),
        "exotics": random.randint(5, 20),
        "members": random.randint(50, 200),
        "activities": random.randint(100, 1000),
        "online": random.randint(10, 50),
        "level": random.randint(5, 10),
        "reputation": random.randint(10000, 50000),
        "item": random.choice(["Gjallarhorn", "Thunderlord", "Last Word", "Vex Mythoclast"]),
        "theme": random.choice(["forging your path", "embracing the Light", "battling the Darkness"]),
        "number": random.randint(20, 25),
        "description": "epic challenges and rewards",
        "features": "new weapons, armor, and activities",
        "challenge1": "Complete Nightfall strikes",
        "challenge2": "Win Crucible matches",
        "challenge3": "Gather resources",
        "activity": "raid completions",
        "focus": "PvP activities",
        "source": "raid bosses",
        "quest": "the current seasonal quest",
        "location": "the Dreaming City",
        "completed": random.randint(50, 200),
        "total": random.randint(300, 600),
        "recent": random.randint(5, 20),
        "percentage": random.randint(30, 80),
        "update": "new exotic quest",
        "announcement": "season extension",
        "patch": "balance changes",
        "streak": random.randint(5, 20),
        "space": random.randint(50, 200),
        "power": random.randint(1800, 2000),
        "upgrades": random.randint(10, 50),
        "quality": random.choice(["excellent", "decent", "needs work"]),
        "mods": random.randint(20, 100),
        "legendaries": random.randint(50, 150)
    }

    for key, value in placeholders.items():
        template = template.replace(f"{{{key}}}", str(value))

    return template

# Map queries to response types
query_mapping = {
    "What's happening in Destiny 2 right now?": "current_events",
    "Show my player stats.": "stats",
    "What's my current inventory?": "inventory",
    "Check clan info.": "clan",
    "Equip this item on my Titan.": "equip",
    "Tell me about the current season.": "season",
    "What are the weekly challenges?": "challenges",
    "How do I get this exotic?": "exotic",
    "What's my light level?": "light",
    "Show me my triumphs.": "triumphs",
    "What's the latest news?": "news",
    "How many wins do I have?": "wins",
    "What's in the vault?": "vault",
    "Tell me about my gear.": "gear",
    "What's the current event?": "event"
}

# Generate dataset
dataset = []
for _ in range(1000):
    query = random.choice(user_queries)
    query_type = query_mapping.get(query, "current_events")
    response = generate_ghost_response(query_type)
    dataset.append({
        "input": f"User: {query}",
        "output": f"Ghost: {response}"
    })

# Save to JSONL file
with open("destiny_dataset.jsonl", "w") as f:
    for item in dataset:
        f.write(json.dumps(item) + "\n")

print("Dataset generated with 1000 examples.")
