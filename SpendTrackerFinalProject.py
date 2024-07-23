import tkinter as tk
import sqlite3

class BudgetApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Spending Tracker")

        # Connect to the database (or create it if it doesn't exist yet)
        self.conn = sqlite3.connect("userAccounts.db")
        self.cursor = self.conn.cursor()

        # Create tables if they don't exist yet either
        self.create_tables()

        # Create GUI buttons and labels for login/register
        self.label = tk.Label(root, text="Welcome to the Spending Tracker. Please login or register to continue:")
        self.label.grid(row=1, column=1, padx=10)

        self.username_entry = tk.Entry(root, width=30)
        self.username_entry.grid(row=3, column=1, padx=10)
        self.username_label = tk.Label(root, text="Username:")
        self.username_label.grid(row=2, column=1, padx=10)

        self.password_entry = tk.Entry(root, width=30, show="*") # Show stars for the password entry
        self.password_entry.grid(row=5, column=1, padx=10)
        self.password_label = tk.Label(root, text="Password:")
        self.password_label.grid(row=4, column=1, padx=10)

        self.login_button = tk.Button(root, text="Login", command=self.login)
        self.login_button.grid(row=6, column=1)

        self.register_button = tk.Button(root, text=" OR Register", command=self.register)
        self.register_button.grid(row=6, column=2)

        self.session_manager = UserSessionManager(self)

    def create_tables(self):
        # Create a table for the user accounts and password (plaintext for demonstration)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE,
                password TEXT
            )
        """)

        # Create a table and column for each users defined budget category and link it to the user table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS budgetCategories (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                categoryName TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Create a table for storing category amounts and link it to the other two tables
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS categoryAmounts (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                category_id INTEGER,
                amount REAL,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (category_id) REFERENCES budgetCategories(id)
            )
        """)

        # Create a table for storing user budgets
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS userBudgets (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                budget REAL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        self.conn.commit() # Commit changes

    def register(self):
        new_username = self.username_entry.get()
        new_password = self.password_entry.get()
        try:
            self.cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (new_username, new_password))
            self.conn.commit()
            print("User registered successfully, please log in to continue")
        except sqlite3.IntegrityError: # Make sure the user name is not already taken
            print("Username already exists. Please create a different one.")

    def login(self):
        existing_username = self.username_entry.get()
        existing_password = self.password_entry.get()
        self.cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (existing_username, existing_password))
        user = self.cursor.fetchone()
        if user:
            print(f"{existing_username} is now logged in!")
            self.session_manager.login(user[0], existing_username)  # Pass the user ID to the session manager
        else:
            print("Incorrect username or password. Please try again.")

    def open_dashboard(self, user_id):
        # Close the login window for now
        self.root.destroy()

        # Open the users dashboard
        self.dashboard_window = tk.Tk()
        self.dashboard_window.title("User Dashboard")

        # Add a frame for the categories and amounts
        self.categories_frame = tk.Frame(self.dashboard_window)
        self.categories_frame.pack()

        # Display the users existing categories and input fields for amounts
        self.display_categories(user_id)

        # Create button to create a new category
        new_category_entry = tk.Entry(self.dashboard_window, width=30)
        new_category_entry.pack()

        create_category_button = tk.Button(self.dashboard_window, text="Create New Category", command=lambda: self.create_budget_category(user_id, new_category_entry.get()))
        create_category_button.pack()

        # Create the button to show and get the total amount
        total_button = tk.Button(self.dashboard_window, text="Show Total", command=lambda: self.amount_manager.show_total(user_id, self.dashboard_window))
        total_button.pack()

        # Make Button to set the users budget
        budget_button = tk.Button(self.dashboard_window, text="Set Budget", command=lambda: self.set_user_budget(user_id))
        budget_button.pack()

        # A Refresh button for clearing the entered values in the entry widgets
        refresh_button = tk.Button(self.dashboard_window, text="Refresh Screen", command=lambda: self.refresh_dashboard(user_id))
        refresh_button.pack()

        # Create a Logout button
        logout_button = tk.Button(self.dashboard_window, text="Logout", command=self.session_manager.logout)
        logout_button.pack()

        self.dashboard_window.mainloop()

    def display_categories(self, user_id):
        # Clear the frame first for now
        for widget in self.categories_frame.winfo_children():
            widget.destroy()

        # Get the users categories
        user_categories = self.get_user_categories(user_id)

        # Display existing categories and create the input fields for amounts
        for category in user_categories:
            category_label = tk.Label(self.categories_frame, text=f"{category}:")
            category_label.pack()

            amount_entry = tk.Entry(self.categories_frame, width=10)
            amount_entry.pack()
            # Create the save button (now refreshes the screen too)
            save_button = tk.Button(self.categories_frame, text="Save", command=lambda cat=category, entry=amount_entry: self.amount_manager.save_amount(user_id, cat, entry.get()))
            save_button.pack()

    def refresh_dashboard(self, user_id):
        self.display_categories(user_id)

    def get_user_categories(self, user_id):
        # Grab the users budget categories from the database
        self.cursor.execute("SELECT categoryName FROM budgetCategories WHERE user_id = ?", (user_id,))
        categories = self.cursor.fetchall()
        return [category[0] for category in categories]

    def create_budget_category(self, user_id, category_name):
        # Add the users new category to the database
        self.cursor.execute("INSERT INTO budgetCategories (user_id, categoryName) VALUES (?, ?)", (user_id, category_name))
        self.conn.commit()
        print(f"Budget category '{category_name}' created successfully!")
        self.refresh_dashboard(user_id)  # Refresh the dashboard after creating a new category instead of making the user click refresh

    def set_user_budget(self, user_id):
        # Add the users budget to the table
        def save_budget():
            budget = float(budget_entry.get())
            self.cursor.execute("INSERT INTO userBudgets (user_id, budget) VALUES (?, ?)", (user_id, budget))
            self.conn.commit()
            print(f"Budget set to {budget}")
            budget_window.destroy()
        #Create Button to save budgete in a new window
        budget_window = tk.Toplevel(self.dashboard_window)
        budget_window.title("Set Budget")
        
        budget_label = tk.Label(budget_window, text="Enter your budget:")
        budget_label.pack()

        budget_entry = tk.Entry(budget_window, width=30)
        budget_entry.pack()

        save_button = tk.Button(budget_window, text="Save Budget", command=save_budget)
        save_button.pack()
# Second class to satisfy requirements 
class CategoryAmountManager:
    def __init__(self, cursor):
        self.cursor = cursor

    def save_amount(self, user_id, category, amount):
        # Save the entered amount for the users selected category
        self.cursor.execute("SELECT id FROM budgetCategories WHERE user_id = ? AND categoryName = ?", (user_id, category))
        category_id = self.cursor.fetchone()[0]
        self.cursor.execute("INSERT INTO categoryAmounts (user_id, category_id, amount) VALUES (?, ?, ?)", (user_id, category_id, amount))
        self.cursor.connection.commit()
        print(f"Saved {amount} for category {category}")

    def show_total(self, user_id, window):
        # Add up and display the total amount spent across all categories
        self.cursor.execute("SELECT SUM(amount) FROM categoryAmounts WHERE user_id = ?", (user_id,))
        total_amount = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT budget FROM userBudgets WHERE user_id = ?", (user_id,))
        budget = self.cursor.fetchone()[0]
        
        remaining_balance = budget - total_amount

        total_label = tk.Label(window, text=f"Total Amount Spent: {total_amount}")
        total_label.pack()

        remaining_label = tk.Label(window, text=f"Remaining Balance: {remaining_balance}")
        remaining_label.pack()

# Create third class to handle login and logout
class UserSessionManager:
    def __init__(self, app):
        self.app = app
        self.current_user_id = None
        self.current_username = None

    def login(self, user_id, username):
        self.current_user_id = user_id
        self.current_username = username
        self.app.open_dashboard(user_id)

    def logout(self):
        self.current_user_id = None
        self.current_username = None
        self.app.dashboard_window.destroy()
        self.app.__init__(tk.Tk())
        print("User logged out successfully")

if __name__ == "__main__":
    root = tk.Tk()
    app = BudgetApp(root)
    app.amount_manager = CategoryAmountManager(app.cursor)
    root.mainloop()

    # Close the database connection to clean up
    app.conn.close()