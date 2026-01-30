import pandas as pd
import random

# --- CONFIGURATION ---
NUM_BOOKS = 30000 

# 1. MASSIVE SUBJECT LIST (New Categories Added)
subjects = {
    "Engineering": ["Thermodynamics", "Fluid Mechanics", "Circuit Theory", "Data Structures", "Concrete Technology", "Python", "Machine Design", "VLSI Design", "Civil Engineering Basics", "Mechanical Vibrations"],
    "Medical": ["Human Anatomy", "Biochemistry", "Pathology", "Pharmacology", "Forensic Medicine", "Microbiology", "Surgery Basics", "Pediatrics", "Neurology", "Cardiology"],
    "Law": ["Constitutional Law", "Criminal Law", "Corporate Law", "Intellectual Property Rights", "Torts", "Contract Law", "International Law", "Family Law"],
    "Architecture": ["Modern Architecture", "Urban Planning", "Interior Design", "Sustainable Design", "History of Architecture", "Landscape Architecture", "Building Construction"],
    "Cooking & Hotel Mgmt": ["French Cuisine", "Indian Spices", "Bakery & Confectionery", "Hotel Housekeeping", "Food Safety", "Culinary Arts", "Vegan Cooking"],
    "Data Science": ["Machine Learning", "Deep Learning", "Neural Networks", "Big Data Analytics", "Statistics for Data Science", "Natural Language Processing", "Computer Vision"],
    "Psychology": ["Cognitive Psychology", "Child Development", "Clinical Psychology", "Behavioral Science", "Social Psychology", "Counseling Techniques"],
    "Commerce": ["Financial Accounting", "Microeconomics", "Business Law", "Marketing Management", "Cost Accounting", "Corporate Tax", "Supply Chain Management"],
    "Competitive Exams": ["UPSC General Studies", "JEE Advanced Physics", "NEET Biology", "CAT Verbal Ability", "GATE Computer Science", "Banking Reasoning", "IELTS Preparation"],
    "Fiction": ["Harry Potter", "Sherlock Holmes", "The Alchemist", "Lord of the Rings", "Pride and Prejudice", "The Great Gatsby", "1984"],
    "History": ["World War II", "Ancient India", "The Cold War", "Modern European History", "The Mughal Empire", "Renaissance Art"],
}

# 2. VARIETY GENERATORS (To ensure uniqueness)
actions = [
    "The Complete Guide to", "Introduction to", "Advanced", "Mastering",
    "Principles of", "Handbook of", "The Future of", "Fundamentals of",
    "Crash Course in", "Essentials of", "The Bible of", "Simplified",
    "Applied", "Theoretical"
]

audiences = [
    "Students", "Beginners", "Engineers", "Doctors", "Aspirants", 
    "Experts", "Professionals", "Dummies", "Kids", "Researchers"
]

editions = ["2024 Edition", "2025 Updated", "Vol. 1", "Vol. 2", "Second Edition", "Revised Edition", "Global Edition", "Standard Edition"]

# --- GENERATOR LOOP ---
titles = []
genres = []
descriptions = []
links = []

print(f"Generating {NUM_BOOKS} unique books... (This takes about 15 seconds)")

for i in range(NUM_BOOKS):
    # Pick random components
    category = random.choice(list(subjects.keys()))
    subject = random.choice(subjects[category])
    action = random.choice(actions)
    audience = random.choice(audiences)
    edition = random.choice(editions) # This ensures uniqueness!
    
    # 1. Unique Title
    # Randomly decide structure to add variety
    if i % 2 == 0:
        title = f"{action} {subject} for {audience} ({edition})"
    else:
        title = f"{subject}: {action} {audience} [{edition}]"
    
    # 2. Genre
    genre = category

    # 3. Description (Keywords for AI)
    desc = f"A comprehensive {category} resource about {subject}. This {edition} covers key concepts, {action.lower()} and real-world applications for {audience}. Top rated by {audience}."
    
    # 4. Link
    link = f"https://www.google.com/search?tbm=bks&q={title.replace(' ', '+').replace('(', '').replace(')', '')}"
    
    titles.append(title)
    genres.append(genre)
    descriptions.append(desc)
    links.append(link)

# --- SAVE ---
# We save it as 'mega_library.csv' so you don't have to change your main code!
df = pd.DataFrame({'Title': titles, 'Genre': genres, 'Description': descriptions, 'Link': links})

# Double check for duplicates just in case
df = df.drop_duplicates(subset=['Title'])

df.to_csv("mega_library.csv", index=False)
print(f"✅ Success! Generated 'mega_library.csv' with {len(df)} unique books.")