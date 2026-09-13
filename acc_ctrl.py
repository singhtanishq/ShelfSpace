import mysql.connector as conn2
from time import sleep
from validate_email import validate_email

# -----------------------------------------------------------------------
'''This function will help the administrator to add new users.
   Here, Username entered will be accepted only if same username is already not present in database.
   Secondly, here email entered will be accepted only if it really exists
   (i.e) the given email-address has an MX record and SMTP server port. Disposable emails will  
   not be accepted here. Module used here is 'validate_email' '''

def Add_new():
    mycon2 = conn2.connect(host="localhost", user="root", password="Rinshu@03", database="book_shop")
    cursor = mycon2.cursor(buffered=True)
    no_user = int(input('Enter number of user you want to add: '))
    for i in range(no_user):
        input_username = input("    Enter Login ID for the user: ")
        cursor.execute(f"SELECT username FROM accounts WHERE username = '{input_username}'")
        data = cursor.fetchone()
        if not data:
            input_password = input("    Enter Password of the user: ")
            input_name = input("    Enter name of the user: ")

            def ent():
                input_email = input("    Enter email of the user: ")
                cursor.execute(f"SELECT * FROM accounts WHERE email = '{input_email}'")
                data2 = cursor.fetchone()
                if data2 != None:
                    print("E-mail Address Already Registered.")
                    ent()
                else:
                    print("Validating Details, please wait.....")
                    try:
                        is_valid = validate_email(input_email)
                        if is_valid:
                            cursor.execute(
                                f"INSERT INTO accounts (username, passwd, name_u, email) VALUES('{input_username}', '{input_password}', "
                                f"'{input_name}', '{input_email}')")
                            mycon2.commit()
                            print("Registering")
                            sleep(2)
                            print(f"Successfully Added User '{input_username}'")
                    except:
                        print("Some Error Occurred.")

            ent()
        else:
            print("User already in database.")
            continue
    mycon2.close()
    return

# -----------------------------------------------------------------------
'''This function will allow the administrator to update the every detail of the user like name, password
   username and email-address. Here email entered will be accepted only if it really exists (i.e) the given 
   email-address has an MX record and SMTP server port. Disposable emails will not be accepted here.
   Modules used here are 'validate_email' and 'mysql.connector' '''

def Update_user():
    mycon2 = conn2.connect(host="localhost", user="root", password="Rinshu@03", database="book_shop")
    cursor = mycon2.cursor(buffered=True)
    no_user = int(input('Enter number of user you want to update: '))
    count = 0
    while count < no_user:
        user_name = str(input("    Enter the username of the user you want to update: "))
        cursor.execute("SELECT * FROM accounts WHERE username = '{}'".format(user_name))
        data = cursor.fetchone()
        if data == None:
            print(f"No user like '{user_name}' exists in database.")  # Checking the wrong Input
            Update_user()
        elif data[0] == 1:
            print("Can't Update user. The specified username is Administrator.")
        else:
            print("     1 -> Update the user's username \n",
                  "    2 -> Update the user's password \n"
                  "     3 -> Update the user's name \n"
                  "     4 -> Update the user's email address")
            choice = int(input("Enter your choice (1 to 4): "))
            if choice == 1:
                new_username = str(input(f"    Enter the new username of {user_name}: "))
                cursor.execute("SELECT * FROM accounts WHERE username = '{}'".format(new_username))
                data2 = cursor.fetchone()
                if data2 == None:
                    cursor.execute(f"UPDATE accounts SET username = '{new_username}' WHERE username = '{user_name}'")
                    mycon2.commit()  # Updating the username
                    print("Successfully Updated")
                else:
                    print("Username Already Exists. \n User Not Updated :(")
            elif choice == 2:
                new_password = str(input(f"    Enter the new password of the {user_name}: "))
                cursor.execute(f"UPDATE accounts SET passwd = '{new_password}' WHERE username = '{user_name}'")
                mycon2.commit()  # Updating the user
                print("Successfully Updated")
            elif choice == 3:
                new_name = str(input(f"    Enter the new name of the {user_name}: "))
                cursor.execute(f"UPDATE accounts SET name_u = '{new_name}' WHERE username = '{user_name}'")
                mycon2.commit()  # Updating the user
                print("Successfully Updated")
            elif choice == 4:
                new_mail = str(input(f"    Enter the new email address of the {user_name}: "))
                cursor.execute(f"SELECT email FROM accounts WHERE email = '{new_mail}'")
                data3 = cursor.fetchone()
                if data3 == None:
                    is_valid = validate_email(new_mail)
                    if is_valid:
                        cursor.execute(f"UPDATE accounts SET email = '{new_mail}' WHERE username = '{user_name}'")
                        mycon2.commit()  # Updating the user
                        print("Successfully Updated")
                    else:
                        print("Invalid Email Address. User not updated :(")
                else:
                    print("Email Address Already registered. \n User Not updated :(")
            else:
                print("Wrong Input")
                Update_user()
        count += 1
    mycon2.close()
    return

# -----------------------------------------------------------------------
''' This function will help administrator to delete any user he/she wants from database
    by entering his/her username if it exists. But admin can't delete the administrator account
    Module used here is 'mysql.connector' '''

def Del_user():
    mycon2 = conn2.connect(host="localhost", user="root", password="Rinshu@03", database="book_shop")
    cursor = mycon2.cursor(buffered=True)
    no_user = int(input("Enter number of accounts you want to delete: "))
    count = 0
    while count < no_user:
        user_name = str(input("    Enter the username of the user you want to delete: "))
        cursor.execute(f"SELECT * FROM accounts WHERE username = '{user_name}'")
        data = cursor.fetchone()
        if data == None:
            print(f"No user like '{user_name}' exists in database.")  # Checking the Wrong Input
            Del_user()
        elif data[0] == 1:
            print("Can't Delete user. The specified username is Administrator.")
        else:
            cursor.execute(f"DELETE FROM accounts where username = '{user_name}'")
            mycon2.commit()  # Deleting the user
            sleep(2)
            print("Successfully Deleted.")
        count += 1
    mycon2.close()
    return

# -----------------------------------------------------------------------
''' This function will allow administrator to view every detail of every user in database. 
    Module used here is mysql.connector '''

def All_u():
    mycon2 = conn2.connect(host="localhost", user="root", password="Rinshu@03", database="book_shop")
    cursor = mycon2.cursor(buffered=True)
    cursor.execute("SELECT * FROM accounts")
    data = cursor.fetchall()
    count = 0
    for row in data:
        tp = row
        count += 1
        print()
        print(f"          User {count}")
        print("      ID             : ", tp[0])
        print("      Username       : ", tp[1])
        print("      Password       : ", tp[2])
        print("      Name           : ", tp[3])
        print("      E-mail Address : ", tp[4])
    mycon2.close()
    return

# -----------------------------------------------------------------------
'''This function will help administrator to view details of the user by entering 
   his/her username if it exists in database.'''

def View_user():
    mycon2 = conn2.connect(host="localhost", user="root", password="Rinshu@03", database="book_shop")
    cursor = mycon2.cursor(buffered=True)
    num = int(input("Enter the number of users of which you want details of: "))
    count = num
    while count != 0:
        user_name = str(input("    Enter the username of the user: "))
        cursor.execute(f"SELECT * FROM accounts WHERE username = '{user_name}'")
        data = cursor.fetchone()
        if not data:
            print("Username specified is invalid. Enter Again.")
            print()
        else:
            print(f"   ID:            {data[0]}")
            print(f"   Username:      {data[1]}")
            print(f"   Name:          {data[3]}")
            print(f"   Email-Address: {data[4]}")
            print()
            count -= 1
    return

# -----------------------------------------------------------------------
'''Sign_Up function will allow any new user running the software to register himself in database.
   For this, they have to create a username, password, give their name and enter their email address which
   really exists as it will be checked then only the user will be registered.
   Module used here is 'validate_email' and 'mysql.connector' '''

def Sign_Up():
    mycon2 = conn2.connect(host="localhost", user="root", password="Rinshu@03", database="book_shop")
    cursor = mycon2.cursor(buffered=True)
    input_username = input("            Create Username (Login ID) : ")
    cursor.execute(f"SELECT * FROM accounts WHERE username = '{input_username}'")
    data = cursor.fetchone()
    if data == None:
        input_password = input("            Create Password: ")
        input_name = input("            Enter your name: ")

        def ent():
            input_email = input("            Enter your email address: ")
            cursor.execute(f"SELECT * FROM accounts WHERE email = '{input_email}'")
            data2 = cursor.fetchone()
            if data2 != None:
                print("E-mail Address Already Registered.")
                ent()
            else:
                print("Validating Details, please wait.....")
                is_valid = validate_email(input_email)
                if is_valid:
                    cursor.execute(
                        f"INSERT INTO accounts (username, passwd, name_u, email) VALUES('{input_username}', "
                        f"'{input_password}', '{input_name}', '{input_email}')")
                    mycon2.commit()
                    print("Registering")
                    sleep(2)
                    print(f"Successfully Added User '{input_username}'")
        ent()
    else:
        print("User Already In Database.")
        print("Try Again")
        Sign_Up()
    mycon2.close()
    return

# ---------------------------------------------------------------------------------------------------
# |                                         End of Module                                           |
# ---------------------------------------------------------------------------------------------------
