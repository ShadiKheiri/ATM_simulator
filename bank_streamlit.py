import streamlit as st
import datetime
import pandas as pd
import regex
from db import cursor, mydb
from backend import(
    create_tables,
    login_customer,
    check_balance,
    view_transactions,
    view_personal_info,
    change_pin,
    verify_forgot_pin_identity,
    forgot_pin,
    update_customer_info,
    register_customer,
    make_transaction,
    update_csv)

# definition to repetative parts
# session_state: streamlit's memory(for temporary information)/ it remembers values between reruns
# resets only when you refresh the page or close the app
# flag: boolean variable in session_state used to control what the app should show
# backend ckecks data, raises errors/ frontend (streamlit) displays messages to the user
# ues .get("key") when checking a key
# use .key = value when setting a key


if st.session_state.get("exit_app"): # if user chose to exit
    # add a bit of vertical space to center the message
    st.write("")
    st.write("")
    st.write("")

    col1, col2, col3 = st.columns([1, 3, 1]) # the middle column is 3 times wider than the side ones
    with col2:
        st.title("You have been logged out successfully.")
        st.subheader("See you next time!")
    st.stop() # stop running the rest of the code for this page


st.set_page_config(page_title="Banking App", layout="wide") # browser tab title/ layout: size of body container
if st.session_state.get("exit_app"): # if exit app, this message will be shown
    st.title("See you next time!")
    st.stop()

# session state keys 
# if thses variables doesn't exsit, create it with a default value
# if flag is not exists, create it (when set it as False, it means it's now off)
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False 
if "account_number" not in st.session_state:
    st.session_state.account_number = None
if "temp_account_number" not in st.session_state:
    st.session_state.temp_account_number = None
if "next_page" not in st.session_state:
    st.session_state.next_page = None

# runs create_tables() if not already done
if "db_init" not in st.session_state: # db_init: flag stored in session state to indicate if DB tables are created
    create_tables()
    st.session_state.db_init = True # create tables is done just once

# centered message
if st.session_state.get("logout_message"):
    st.write("")
    st.write("")
    st.write("")

    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.title("You have been logged out successfully.")
        st.subheader("See you next time!")

        if st.button("Back to Login"):
            st.session_state.logout_message = False # is linked to teh siebar radio because of key="option"
            st.session_state.option = "Login Existing Customer"  # radio button in the sidebar appears with "Login Existing Customer" already selected
            st.rerun() # restarts the script
    st.stop()


# if "Yes" after registration 
if st.session_state.get("goto_login_after_registration"): # user just finished registration and wants to log in immediately using the new account
    st.title("Login to Your New Account")
    account_number = st.text_input("Account Number", value=st.session_state.temp_account_number)
    pin = st.text_input("PIN", type="password")

    if st.button("Login"):
        success, acc_number = login_customer(cursor, account_number, pin) # this checks the credentials in database
        if success:
            st.session_state.logged_in = True # user is authenticated
            st.session_state.account_number = acc_number # store which user is logged in
            st.session_state.show_welcome = True # show welcome page
            # pop(key) removes a key from a dictionary
            st.session_state.pop("goto_login_after_registration") # only needed after registration
            st.session_state.pop("temp_account_number")
            st.rerun() # refresh the UI
        else:
            st.error("Invalid account number or PIN.")
    st.stop() # stop everything below this code from running

# if "No" after registration
if st.session_state.get("thank_you_after_registration"):
    col1, col2, col3 = st.columns([1,2,1])
    with col2: # everything inside this block should appear inside column 2 (middle column)
        st.title("Thanks for using our ATM")
        st.subheader("See you next time!")
    st.session_state.pop("thank_you_after_registration") # remove temporary flag
    st.session_state.pop("temp_account_number") # remove temporary flag
    st.stop() # nothing below this line will be shown

#  navigation handoff
if st.session_state.get("nav_to"):
    st.session_state.option = st.session_state.pop("nav_to")  # apply target

# main options __________________________________________________________________________
if not st.session_state.logged_in:
    options = ["Register New Customer", "Login Existing Customer", "Forgot PIN", "Exit"]

    if "option" not in st.session_state:
        st.session_state.option = "Login Existing Customer" # sidebar by default has this option chosen

    st.sidebar.subheader("Choose an Option")
    option = st.sidebar.radio("", options, key="option") # streamlit authomatically stores the selected value in st.session_state.option

# register new customer__________________________________________________________________
    if option == "Register New Customer":
        st.header("Register New Customer")

        if "post_registration" in st.session_state: # the user already completed the registration form successfully
            # New page after registration
            st.success(f"Registration successful! Your account number is: {st.session_state.temp_account_number}")
            choice = st.radio("**Do you want to log in to your account now?**", ["Yes", "No"])

            if st.button("Continue"):
                if choice == "Yes":
                    # go to login page
                    st.session_state.logged_in = False  # Not logged in yet, will login next
                    st.session_state.goto_login_after_registration = True # go directly to the special login page with a pre-filled account number
                    st.session_state.pop("post_registration") # remove post-registration state(because we are done with it and prevents re-showing)
                    st.rerun() # rerun the whole app because we need to show the login page
                else:
                    # show thank you page
                    st.session_state.thank_you_after_registration = True
                    st.session_state.pop("post_registration") # remove post_registration flag
                    st.rerun()

        else:
            # form: all input is submitted at once, only when the uesr clicks the submit button
            with st.form("register_form"): # st.form: group multiple input widgets
                first_name = st.text_input("First Name", placeholder="e.g. Shadi")
                last_name = st.text_input("Last Name", placeholder="e.g. Kheiri")
                dob = st.date_input("Date of Birth", min_value=datetime.date(1900, 1, 1), max_value=datetime.date.today())
                app = st.text_input("Apartment Number (optional)", placeholder="e.g., 12A or 12")
                building = st.text_input("Building Number", placeholder="12")
                street = st.text_input("Street Name", placeholder="e.g. Saint Cathrine")
                city = st.text_input("City", placeholder="Montreal")
                province = st.selectbox("Province", [
                    "Alberta", "British Columbia", "Manitoba", "New Brunswick", "Newfoundland and Labrador",
                    "Nova Scotia", "Ontario", "Prince Edward Island", "Quebec", "Saskatchewan"])
                postal_code = st.text_input("Postal Code", placeholder="e.g. A1B 2C3").upper()
                phone = st.text_input("Phone Number (Optional)", placeholder="e.g. 1234567890")
                email = st.text_input("Email (Optional)", placeholder="e.g. example@gmail.com")
                pin = st.text_input("4-digit PIN", type="password", placeholder="1234") # type=password: hide input
                submitted = st.form_submit_button("Register")

            if submitted:
                try:
                    if building and regex.fullmatch(r"^\d+\s?[A-Za-z]?$", building): # one or more digits, zero or more space, one letter
                        building = regex.sub(r"^(\d+)\s*([A-Za-z])$", r"\1 \2", building).upper() # sub: find and replace using regex pattern

                    # call backend to register customer
                    account_number = register_customer(
                        first_name.strip(), last_name.strip(), dob.strftime("%Y-%m-%d"),
                        app.strip(), building.strip(), street.strip(), city.strip(), province.strip(), postal_code.strip(), 
                        phone.strip(), email.strip(), pin.strip()
                    )

                    st.session_state.temp_account_number = account_number 
                    st.session_state.post_registration = True # we just registered, so next page is post-registration page
                    update_csv()  # update CSV after registration
                    st.rerun() # because we want to show the post-registration page

                except ValueError as e:
                    errors = e.args[0] # extract the error message (every python exception stores its values in a tuple called args)
                    if isinstance(errors, list): # Check if errors is a list
                        for err in errors:
                            st.error(err)
                    else:
                        st.error(errors)
                except Exception as e:
                    st.error("Unexpected error occurred during registration.")
                    st.text(str(e)) # converts exception to string and displays it

# login existing customer_______________________________________________________________________
    elif option == "Login Existing Customer":
        st.header("Login")
        account_number = st.text_input("Account Number", placeholder="10001")
        pin = st.text_input("PIN", type="password", placeholder="1234")

        if st.button("Login"):
            try:
                # call login_customer in the backend
                success, acc_number = login_customer(cursor, account_number, pin)
                # success, acc_number=backend output
                if success: # did the username and pin matches?
                    # session_state=app remembers state after refresh
                    st.session_state.logged_in = True # user is verified
                    st.session_state.account_number = acc_number  # store which user is logged in
                    st.session_state.show_welcome = True  # show welcome message
                    st.rerun()
                else:
                    st.error("Invalid account number or PIN.")
            except Exception as e:
                st.error("Unexpected error during login.")
                st.text(str(e))

# forgot PIN__________________________________________________________________________________________ 
    elif option == "Forgot PIN":
        st.header("Forgot PIN")

        st.session_state.setdefault("forgot_pin_verified", False)
        st.session_state.setdefault("forgot_pin_reset_done", False)

        if st.session_state.forgot_pin_reset_done: # if the PIN was reset, show success page
            st.success("Your PIN has been reset successfully. You can now log in.")
            if st.button("Back to Login"):
                # clear all temporary values
                st.session_state["forgot_pin_verified"] = False
                st.session_state["forgot_pin_reset_done"] = False
                st.session_state.pop("temp_account_number", None)
                st.session_state.nav_to = "Login Existing Customer" # immediately go to Login Existing Customer after rerun
                st.rerun() # rerun the app
            st.stop() # stop/ don't show the steps

        # verify identity 
        st.subheader("Step 1: Verify your identity")
        account_number = st.text_input("Account Number", placeholder="e.g. 10001")
        first_name = st.text_input("First Name", placeholder="e.g. Shadi")
        last_name = st.text_input("Last Name", placeholder="e.g. Kheiri")
        dob = st.date_input(
            "Date of Birth",
            min_value=datetime.date(1900, 1, 1),
            max_value=datetime.date.today())

        if st.button("Verify Identity"):
            if not (account_number and first_name and last_name):
                st.error("Account number, first name and last name are required.")
            else:
                # call backend function
                ok, msg = verify_forgot_pin_identity(cursor,
                    account_number.strip(),
                    first_name.strip(),
                    last_name.strip(),
                    dob.strftime("%Y-%m-%d"))
                
                if ok:
                    # if identity is correct
                    st.session_state.forgot_pin_verified = True
                    st.session_state.temp_account_number = account_number.strip()
                    st.success("Identity verified. Now set a new PIN below.")
                else:
                    st.session_state.forgot_pin_verified = False # if not verified
                    st.error(msg)

        # change PIN (only if verified)
        if st.session_state.forgot_pin_verified:
            st.subheader("Step 2: Set a new PIN")

            new_pin = st.text_input("New PIN (4 digits)", type="password", placeholder="1234")
            confirm_pin = st.text_input("Confirm New PIN", type="password", placeholder="1234")

            if st.button("Reset PIN"):
                if not (new_pin and confirm_pin):
                    st.error("Both PIN fields are required.")
                elif new_pin != confirm_pin:
                    st.error("New PINs do not match.")
                elif not new_pin.isdigit() or len(new_pin) != 4:
                    st.error("New PIN must be exactly 4 digits.")
                else:
                    try:
                        success, msg = forgot_pin(cursor, mydb, st.session_state.temp_account_number,
                            first_name.strip(),
                            last_name.strip(),
                            dob.strftime("%Y-%m-%d"),
                            new_pin.strip(),)
                        
                        if success:
                            st.session_state.forgot_pin_reset_done = True # success screen
                            st.rerun()
                        else:
                            st.error(msg)
                    except Exception as e:
                        st.error("Something went wrong during PIN reset.")
                        st.text(str(e))

 # exit_____________________________________________________________________________________
    elif option == "Exit":
        st.session_state.exit_app = True # show the exit page next time the app runs
        st.rerun() # immediately rerun the app

## post-login menu_____________________________________________________________________________
if st.session_state.logged_in: # check if the user logged in
    st.sidebar.subheader(f"**Logged in as:** {st.session_state.account_number}") # show user info in the sidebar
    st.sidebar.markdown("---")
    st.sidebar.subheader("Account Menu")
    menu = st.sidebar.selectbox("",[
        "Check Balance",
        "Make Transaction",
        "View Transactions",
        "View Personal Info",
        "Update Personal Info",
        "Change PIN",
        "Logout"
    ])

    if st.session_state.get("show_welcome", False): # show welcome message once after login/ checking a key
        st.title(f"Welcome to our ATM") 
        st.subheader("Please select an option from the left menu to continue.")
        st.session_state.show_welcome = False # reset so it doesn't show again/ setting a key

    else:

### check balance______________________________________________________________________________
        if menu == "Check Balance":
            st.title("Check Balance")
            try:
                # call check_balance in the backend
                balance = check_balance(cursor, st.session_state.account_number) # check the balance
                if balance is not None:
                    st.subheader(f"Your current balance is: ${balance:,.2f}")
                else:
                    st.error("Account not found.")
            except Exception as e:
                st.error("Failed to retrieve balance.")
                st.text(str(e))

### view transactions______________________________________________________________________________
        elif menu == "View Transactions":
            st.title("View Transactions")
            st.subheader("Filter Options")

            # store default filter values (used when user clicks Reset Filter)
            defaults = {
                "filter_start": datetime.date(2000, 1, 1),
                "filter_end": datetime.date.today(),
                "filter_type": "All",
                "filter_min": 0.00,
                "filter_max": 10_000.00,
                "filter_sort": "Newest First",
                "filter_n": 10,
                "filter_scope": "All Transactions",}

            for key, value in defaults.items():
                if key not in st.session_state:
                    st.session_state[key] = value

            if st.session_state.get("reset_filters", False): # checking reset filter
                st.session_state.update(defaults) # apply all default filter values
                st.session_state.reset_filters = False # turn reset flag off
                st.rerun() # update immediately with default value

            col1, col2 = st.columns(2) # splitting the screen into 2 side-by-side sections

            start_date = col1.date_input("Start Date", key="filter_start")
            end_date = col2.date_input("End Date", key="filter_end")
            transaction_type = st.selectbox("Transaction Type", ["All", "Deposit", "Withdrawal"], key="filter_type")
            col3, col4 = st.columns(2) # splitting the screen into 2 side-by-side sections
            min_amount = col3.number_input("Minimum Amount", min_value=0.00, step=0.01, key="filter_min")
            max_amount = col4.number_input("Maximum Amount", max_value=10_000.00, step=0.01, key="filter_max")
            sort_option = st.selectbox(
                "Sort By",
                ["Newest First", "Oldest First", "Highest Amount", "Lowest Amount"],
                key="filter_sort")

            # let user choose N (default 10)
            n_last = st.number_input(
                "N: Number of last transactions",
                min_value=1,
                step=1,
                key="filter_n")

            # allow user to choose all vs last N
            filter_scope = st.selectbox(
                "Apply filters to",
                ["All Transactions", "Last N Transactions"],
                key="filter_scope")

            # apply filter button
            apply_filter = st.button("Apply Filter")

            # reset filter button
            reset_filter = st.button("Reset Filter")

            if reset_filter:
                st.session_state.reset_filters = True
                st.rerun()

            try:
                # call view_transactions in the backend
                df = view_transactions(st.session_state.account_number)
                df["timestamp"] = pd.to_datetime(df["timestamp"])

                if apply_filter:
                    if filter_scope == "Last N Transactions":
                        df = df.sort_values(by="timestamp", ascending=False).head(n_last)

                    # date range
                    df = df[(df["timestamp"].dt.date >= start_date) &
                            (df["timestamp"].dt.date <= end_date)]

                    # transaction type
                    if transaction_type != "All":
                        df = df[df["type"].str.lower() == transaction_type.lower()]

                    # amount range
                    df = df[(df["amount"] >= min_amount) &
                            (df["amount"] <= max_amount)]

                    # sorting
                    if sort_option == "Newest First":
                        df = df.sort_values(by="timestamp", ascending=False)
                    elif sort_option == "Oldest First":
                        df = df.sort_values(by="timestamp", ascending=True)
                    elif sort_option == "Highest Amount":
                        df = df.sort_values(by="amount", ascending=False)
                    elif sort_option == "Lowest Amount":
                        df = df.sort_values(by="amount", ascending=True)

                else:
                    df = df.sort_values(by="timestamp", ascending=False).head(10)

                df["amount"] = df["amount"].apply(lambda x: f"${x:,.2f}") # change to format 100 -> $100.00
                st.dataframe(df)

                csv = df.to_csv(index=False).encode("utf-8") # convert the filtered DataFrame to CSV/ encode: streamlit's downalod button requires bytes, not a string
                st.download_button(
                    "Download Transaction History",
                    data=csv,
                    file_name="Transaction History.csv",
                    mime="text/csv") # tells browser it's a CSV file (to have correct file type)

            except Exception as e:
                st.error("Failed to filter transactions.")
                st.text(str(e))

### view personal info_______________________________________________________________________
        elif menu == "View Personal Info":
            st.title("View Personal Information")
            try:
                # call view_personal_info in the backend
                info = view_personal_info(cursor, st.session_state.account_number)
                if isinstance(info, dict): # check if info is a dictionary
                    for key, value in info.items(): # display each field
                        st.write(f"**{key}**: {value}")
                else:
                    st.warning("No personal info found.")
            except Exception as e:
                st.error("Could not retrieve personal information.")
                st.text(str(e))

### update personal info_______________________________________________________________________
        elif menu == "Update Personal Info":
            st.title("Update Personal Information")
            app = st.text_input("New Apartment Number", placeholder="e.g. 12A or 12")
            building = st.text_input("New Building Number", placeholder="e.g. 12")
            street = st.text_input("New Street Name", placeholder="Sainte Cathrine")
            city = st.text_input("New City", placeholder="Montreal")
            province = st.selectbox("New Province", [
                "Alberta", "British Columbia", "Manitoba", "New Brunswick", "Newfoundland and Labrador",
                "Nova Scotia", "Ontario", "Prince Edward Island", "Quebec", "Saskatchewan"])
            postal_code = st.text_input("New Postal Code", placeholder="e.g. A1B 2C3").upper()
            phone = st.text_input("New Phone", placeholder="e.g. 1234567890")
            email = st.text_input("New Email", placeholder="e.g. example@gmail.com")

            if st.button("Update Info"):
                try:
                    # validation (same as registration)
                    errors = []
                    if app and not regex.fullmatch(r"^\d+( [A-Za-z])?$", app):
                        errors.append("Invalid apartment number format.")
                    if building and not regex.fullmatch(r"^\d+[A-Z]?$", building.strip()):
                        errors.append("Invalid building number format.")
                    if street and not regex.fullmatch(r"^[\p{L}]+([\- ]?[\p{L}\d])*$", street):
                        errors.append("Invalid street name.")
                    if city and not regex.fullmatch(r"^[\p{L}\s\-]+$", city):
                        errors.append("Invalid city name.")
                    if postal_code and not regex.fullmatch(r"^[A-Z]\d[A-Z] \d[A-Z]\d$", postal_code):
                        errors.append("Invalid postal code.")
                    if phone and (not phone.isdigit() or len(phone) != 10):
                        errors.append("Phone must be 10 digits.")
                    if email and (not regex.match(r"^[^@]+@[^@]+\.[^@]{2,}$", email) or len(email) < 6):
                        errors.append("Invalid email address.")

                    if errors:
                        for e in errors:
                            st.error(e)
                    else:
                        # call update_customer_info in the backend
                        if update_customer_info(cursor, st.session_state.account_number,
                            # paramter name in backend function = variable from streamlit form
                            email=email,
                            phone=phone,
                            app=app,
                            building=building,
                            street=street,
                            city=city,
                            province=province,
                            postal_code=postal_code):
                            st.success("Information updated successfully.")
                        else:
                            st.error("update failed.")
                except Exception as e:
                    st.error("Unexpected error.")
                    st.text(str(e))

### make transaction_________________________________________________________________
        elif menu == "Make Transaction":
            st.title("Make Transaction")
            transaction_label = st.radio("**Select Transaction Type**", ["Deposit", "Withdrawal"])
            transaction_type = transaction_label.lower()

            amount = st.number_input("Enter Amount", min_value=None, step=0.01, format="%.2f")

            if st.button("Submit Transaction"):
                # validate amount
                if amount is None or amount <= 0:
                    st.error("Transaction failed: Amount must be a positive number.")
                    st.stop() # stop execution

                elif amount < 0.1:
                    st.error("Transaction failed: Minimum allowed amount is 0.10.")
                    st.stop() # stop execution

                try:
                    # call make_transaction in the backend
                    result = make_transaction(cursor, st.session_state.account_number,
                        transaction_type.title(),
                        amount)
                    st.success(result)

                except ValueError as e:
                    st.error(f"Transaction failed: {str(e)}")

                except Exception as e:
                    st.error("Transaction failed.")
                    st.text(str(e))

            try:
                # call check_balance in the backend
                balance = check_balance(cursor, st.session_state.account_number) # check the balance
                if balance is not None:
                    st.write(f"**Your current balance is: ${balance:,.2f}**")
                else:
                    st.error("Account not found.")
            except Exception as e:
                st.error("Failed to retrieve balance.")
                st.text(str(e))
                
### change PIN_____________________________________________________________________________
        elif menu == "Change PIN":
            st.title("Change PIN")
            old_pin = st.text_input("Old PIN (4 Digits)", type="password", placeholder="1234")
            new_pin = st.text_input("New PIN (4 Digits)", type="password", placeholder="1234")
            confirm_pin = st.text_input("Confirm New PIN", type="password", placeholder="1234")

            if st.button("Change PIN"):
                if not old_pin or not new_pin or not confirm_pin:
                    st.error("All fields are required.")
                elif new_pin != confirm_pin:
                    st.error("New PINs do not match. Try again.")
                elif not new_pin.isdigit() or len(new_pin) != 4:
                    st.error("New PIN must be exactly 4 digits.")
                elif old_pin == new_pin:
                    st.error("New PIN must be different from Old PIN.")
                else:
                    try:
                        # call change_pin in the backend
                        result = change_pin(cursor, st.session_state.account_number, old_pin, new_pin)
                        if "success" in result.lower():
                            st.success(result)
                        else:
                            st.error(result)
                    except Exception as e:
                        st.error("Failed to change PIN.")
                        st.text(str(e))

### logout____________________________________________________________________________________
        elif menu == "Logout":
            st.session_state.logged_in = False # end the logged_in session
            st.session_state.account_number = None # clear which account was logged in
            st.session_state.logout_message = True # show logout message on next rerun
            st.rerun() # rerun the app immediately