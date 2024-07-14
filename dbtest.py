#wip databse
# Features currently are: create user, login user, create users budget categories
# still need to: 
# allow each user to add an amount to each category 
# allow the user to tally the amounts spent from each category
# allow the user to define a monthly budget and compare it to the tally of spent amounts
# allow the user to remove a category
# allow the user to generate a graph (pie graph?) of the categories and spent amounts to compare to the budget
# allow for GUI
import sqlite3

# Connect to the database (or create it if it doesn't exist)
conn = sqlite3.connect("userAccounts.db")
cursor = conn.cursor()

# Create a table for the users account
# Currently using plaintext, would be more realistic to use a hash or something encrypted
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE,
        password TEXT
    )
""")

# Create a table for each user-defined budget category
cursor.execute("""
    CREATE TABLE IF NOT EXISTS budgetCategories (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        categoryName TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
""")
conn.commit()

def registerUser(username, password): # Function for allowing the user to register their account
    try: # try in case invalid entry
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit() # Commit to db
        print("User registered successfully, please login to continue")
    except sqlite3.IntegrityError:
        print("Username already exists. Please create a different one.")

def loginUser(username, password): # Let user login
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    if user:
        print(f" {username} is now logged in!")
        return user[0]  # Return the users id
    else:
        print("Invalid username or password. Please try again.")
        return None # Return none so user can try again 

def createBudgetCategory(user_id, categoryName): # Lets the user create their budget categories
    cursor.execute("INSERT INTO budgetCategories (user_id, categoryName) VALUES (?, ?)", (user_id, categoryName))
    conn.commit()
    print(f"Budget category '{categoryName}' created successfully!")

def getUserCategories(user_id): # Gets the users categories 
    cursor.execute("SELECT categoryName FROM budgetCategories WHERE user_id = ?", (user_id,))
    categories = cursor.fetchall() # Fetch all categories
    return [category[0] for category in categories] # Show all the categories

# Proof of concept in terminal
if __name__ == "__main__":
    user_id = None  # Init user_id for later
    while True:
        choice = input("Choose an option (1: Register, 2: Login, 3: Create Budget Category, 4: View My Categories, q: Quit): ")
        if choice == "1":
            newUsername = input("Enter a username ")
            newPassword = input("Enter a password ")
            registerUser(newUsername, newPassword) # create the new user
        elif choice == "2":
            existingUsername = input("Enter your username ")
            existingPassword = input("Enter your password ")
            user_id = loginUser(existingUsername, existingPassword) #login the existing user
        elif choice == "3":
            if user_id:
                categoryName = input("Enter a budget category name to create a new category ")
                createBudgetCategory(user_id, categoryName) # Create the categort for the user
            else:
                print("Please log in first.")
        elif choice == "4":
            if user_id: # Checking if signed in kinda wonky because the terminal doesnt really look different atm
                userCategories = getUserCategories(user_id) 
                print("Your budget categories are ")
                for category in userCategories:
                    print(f"- {category}")
            else:
                print("Please log in first.")
        elif choice.lower() == "q":
            break
        else:
            print("Invalid choice. Please try again.")

# Close the database connection Should probably open and close it with each interaction but would also add a lot of lines and prob doesnt really make a difference 
conn.close()