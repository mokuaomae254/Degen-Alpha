
#first working login
import hashlib
def make_hashes(password):
	return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password,hashed_text):
	if make_hashes(password) == hashed_text:
		return hashed_text
	return False
# DB Management
import sqlite3 
conn = sqlite3.connect('data.db')
c = conn.cursor()
# DB  Functions
def create_usertable():
	c.execute('CREATE TABLE IF NOT EXISTS userstable(username TEXT,password TEXT)')


def add_userdata(username,password):
	c.execute('INSERT INTO userstable(username,password) VALUES (?,?)',(username,password))
	conn.commit()

def login_user(username,password):
	c.execute('SELECT * FROM userstable WHERE username =? AND password = ?',(username,password))
	data = c.fetchall()
	return data


def view_all_users():
	c.execute('SELECT * FROM userstable')
	data = c.fetchall()
	return data

import pandas as pd
import streamlit as st


def main():
    """Simple Login App"""

    # 1. Initialize session state variables if they don't exist
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if "username" not in st.session_state:
        st.session_state["username"] = None

    menu = [
        "Home",
        "Login",
        "SignUp",
        "Logout",
        "Reset Password",
        
    ]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Home":
        scrapping()

    elif choice == "Login":
        st.sidebar.subheader("Login Section")

        # If user is already logged in, show status
        if st.session_state["logged_in"]:
            st.sidebar.success(
                f"Already logged in as: {st.session_state['username']}"
            )
        else:
            username_input = st.sidebar.text_input("User Name")
            password_input = st.sidebar.text_input("Password", type="password")

            if st.sidebar.button("Login"):
                create_usertable()
                hashed_pswd = make_hashes(password_input)

                # Validate user credentials
                result = login_user(
                    username_input, check_hashes(password_input, hashed_pswd)
                )

                if result:
                    # SAVE STATE TO PERSIST ACROSS RERUNS
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = username_input
                    st.sidebar.success(f"Logged In as {username_input}")
                    st.rerun()
                else:
                    st.sidebar.warning("Incorrect Username/Password")

        # If logged in successfully, show main app features

        if st.session_state["logged_in"]:

            # 1. Dynamically build available tasks based on user role
            available_tasks = ["Qualitative Analysis", "Quantitative Analysis"]

            # Show "Profiles" only to admin
            if st.session_state["username"] == "mokua254":
                available_tasks.append("Profiles")

            # Add "Book an Appointment" for everyone
            available_tasks.append("Book an Appointment")

            task = st.selectbox("Task", available_tasks)

            # -------------------------------------------------------------------------
            # Task Handlers
            # -------------------------------------------------------------------------
            if task == "Qualitative Analysis":
                st.subheader("Add Your Post")
                investor_connect2()

                comments = st.text_input("Leave a Comment Below: ")
                st.button("Submit Comment")
                social_medialinks()

            elif task == "Quantitative Analysis":
                st.subheader("Quantitative Analysis")
                crypto_quantitative_analysis()

            elif task == "Profiles":
                if st.session_state["username"] == "mokua254":
                    st.subheader("User Profiles")
                    user_result = view_all_users()
                    clean_db = pd.DataFrame(
                        user_result, columns=["Username", "Password"]
                    )
                    st.dataframe(clean_db)
                else:
                    st.warning("Cannot access profiles.")

            elif task == "Book an Appointment":
                st.subheader("Get an expert's insights")

                # Admin Access Prompt
                if st.session_state["username"] == "mokua254":
                    st.info("ℹ️ You are logged in as Admin (`mokua254`). This feature is designed for clients.")
                    admin_access = st.checkbox("Preview Client Booking Interface")

                    if admin_access:
                        booking_consultation()
                    else:
                        st.caption("Check the box above if you want to view or test the booking flow.")
                else:
                    # Render directly for clients
                    booking_consultation()

       
    elif choice == "Logout":
        st.subheader("Logout Section")
        if st.session_state["logged_in"]:
            if st.button("Confirm Logout"):
                st.session_state["logged_in"] = False
                st.session_state["username"] = None
                st.success("You have been logged out.")
                st.rerun()
        else:
            st.info("You are not logged in.")

    elif choice == "Reset Password":
        st.subheader("Reset Password")
        username = st.text_input("Username")
        old_password = st.text_input("Old Password", type="password")
        new_password = st.text_input("New Password", type="password")

        if st.button("Reset"):
            create_usertable()
            hashed_pswd = make_hashes(old_password)

            result = login_user(
                username, check_hashes(old_password, hashed_pswd)
            )
            if result:
                reset_password(username, new_password)
                st.success("Password successfully reset!")
            else:
                st.warning("Incorrect Username/Password")

    elif choice == "SignUp":
        st.subheader("Create New Account")
        new_user = st.text_input("Username")
        new_password = st.text_input("Password", type="password")

        if st.button("Signup"):
            create_usertable()
            add_userdata(new_user, make_hashes(new_password))
            st.success("You have successfully created a valid Account")
            st.info("Go to Login Menu to login")

    

    
if __name__ == "__main__":
    main()


#second working login


import hashlib
import sqlite3
import pandas as pd
import streamlit as st

# DB Management Helper Functions
def get_db_connection():
    return sqlite3.connect('data.db', check_same_thread=False)

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def create_usertable():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS userstable(username TEXT UNIQUE, password TEXT)')
    conn.commit()
    conn.close()

def add_userdata(username, password):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('INSERT INTO userstable(username, password) VALUES (?,?)', (username, password))
    conn.commit()
    conn.close()

def login_user(username, hashed_password):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM userstable WHERE username = ? AND password = ?', (username, hashed_password))
    data = c.fetchall()
    conn.close()
    return data

def view_all_users():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT username, password FROM userstable')
    data = c.fetchall()
    conn.close()
    return data

def reset_password(username, new_password):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('UPDATE userstable SET password = ? WHERE username = ?', (make_hashes(new_password), username))
    conn.commit()
    conn.close()


def main():
    """Simple Login App"""
    create_usertable()

    # 1. Initialize session state variables if they don't exist
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if "username" not in st.session_state:
        st.session_state["username"] = None

    menu = [
        "Home",
        "Login",
        "SignUp",
        "Logout",
        "Reset Password",
    ]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Home":
        st.title("Home")
        scrapping()

    elif choice == "Login":
        st.sidebar.subheader("Login Section")

        # If user is already logged in, show status
        if st.session_state["logged_in"]:
            st.sidebar.success(f"Already logged in as: {st.session_state['username']}")
        else:
            username_input = st.sidebar.text_input("User Name").strip()
            password_input = st.sidebar.text_input("Password", type="password")

            if st.sidebar.button("Login"):
                hashed_pswd = make_hashes(password_input)

                # FIXED: Compare the single hash directly with the database
                result = login_user(username_input, hashed_pswd)

                if result:
                    # SAVE STATE TO PERSIST ACROSS RERUNS
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = username_input
                    st.sidebar.success(f"Logged In as {username_input}")
                    st.rerun()
                else:
                    st.sidebar.warning("Incorrect Username/Password")

        # If logged in successfully, show main app features
        if st.session_state["logged_in"]:

            # Dynamically build available tasks based on user role
            available_tasks = ["Qualitative Analysis", "Quantitative Analysis"]

            # Show "Profiles" only to admin
            if st.session_state["username"] == "mokua254":
                available_tasks.append("Profiles")

            # Add "Book an Appointment" for everyone
            available_tasks.append("Book an Appointment")

            task = st.selectbox("Task", available_tasks)

            # -------------------------------------------------------------------------
            # Task Handlers
            # -------------------------------------------------------------------------
            if task == "Qualitative Analysis":
                st.subheader("Add Your Post")
                investor_connect2()

                comments = st.text_input("Leave a Comment Below: ")
                st.button("Submit Comment")
                social_medialinks()

            elif task == "Quantitative Analysis":
                st.subheader("Quantitative Analysis")
                crypto_quantitative_analysis()

            elif task == "Profiles":
                if st.session_state["username"] == "mokua254":
                    st.subheader("User Profiles")
                    user_result = view_all_users()
                    clean_db = pd.DataFrame(user_result, columns=["Username", "Hashed Password"])
                    st.dataframe(clean_db)
                else:
                    st.warning("Cannot access profiles.")

            elif task == "Book an Appointment":
                st.subheader("Get an expert's insights")

                # Admin Access Prompt
                if st.session_state["username"] == "mokua254":
                    st.info("ℹ️ You are logged in as Admin (`mokua254`). This feature is designed for clients.")
                    admin_access = st.checkbox("Preview Client Booking Interface")

                    if admin_access:
                        booking_consultation()
                        admin_dashboard()
                    else:
                        st.caption("Check the box above if you want to view or test the booking flow.")
                else:
                    # Render directly for clients
                    booking_consultation()

    elif choice == "Logout":
        st.subheader("Logout Section")
        if st.session_state["logged_in"]:
            if st.button("Confirm Logout"):
                st.session_state["logged_in"] = False
                st.session_state["username"] = None
                st.success("You have been logged out.")
                st.rerun()
        else:
            st.info("You are not logged in.")

    elif choice == "Reset Password":
        st.subheader("Reset Password")
        username = st.text_input("Username").strip()
        old_password = st.text_input("Old Password", type="password")
        new_password = st.text_input("New Password", type="password")

        if st.button("Reset"):
            hashed_old_pswd = make_hashes(old_password)
            result = login_user(username, hashed_old_pswd)
            if result:
                reset_password(username, new_password)
                st.success("Password successfully reset!")
            else:
                st.warning("Incorrect Username/Password")

    elif choice == "SignUp":
        st.subheader("Create New Account")
        new_user = st.text_input("Username").strip()
        new_password = st.text_input("Password", type="password")

        if st.button("Signup"):
            if new_user and new_password:
                try:
                    add_userdata(new_user, make_hashes(new_password))
                    st.success("You have successfully created an account!")
                    st.info("Go to the Login menu to log in.")
                except sqlite3.IntegrityError:
                    st.error("Username already exists. Please choose a different one.")
            else:
                st.warning("Please fill in both fields.")

if __name__ == "__main__":
    main()


#my new login on postgress
setting up postgres database connection and user authentication using psycopg2 and streamlit.
Set up this Neon project in the current working directory.

1. `npm i -g neon@latest && neon login`
2. `neon skills -y`
3. `neon mcp -y`
4. `neon link --project-id aged-wave-52733639 --branch production -y`
5. `neon config init`
6. Update `neon.ts`:

```ts
import { defineConfig } from "@neon/config/v1";

export default defineConfig({});
```

7. `neon deploy`

my old login on sqlite3


"""   
import hashlib
import sqlite3
import pandas as pd
import streamlit as st



def make_hashes(password):
	return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password,hashed_text):
	if make_hashes(password) == hashed_text:
		return hashed_text
	return False
# DB Management
import sqlite3 
conn = sqlite3.connect('data.db')
c = conn.cursor()
# DB  Functions
def create_usertable():
	c.execute('CREATE TABLE IF NOT EXISTS userstable(username TEXT,password TEXT)')


def add_userdata(username,password):
	c.execute('INSERT INTO userstable(username,password) VALUES (?,?)',(username,password))
	conn.commit()

def login_user(username,password):
	c.execute('SELECT * FROM userstable WHERE username =? AND password = ?',(username,password))
	data = c.fetchall()
	return data


def view_all_users():
	c.execute('SELECT * FROM userstable')
	data = c.fetchall()
	return data

import pandas as pd
import streamlit as st

"""



     
