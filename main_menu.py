# Python Modules
import mysql.connector as conn
import time

# Project Modules
import books
import orders
import acc_ctrl

start_time = time.time()

print(" -----------------------  [ Welcome to S & T Book Shop Management System ]  -----------------------")


def Main_menu(a, b, c):
    # Login in with Account
    mycon = conn.connect(host="localhost", user="root", password="Rinshu@03", database="book_shop")
    login = 0
    while login != 1:  # Checking
        cursor = mycon.cursor()  # for a valid user
        cursor.execute(f"select * from accounts where username = '{a}' and passwd = '{b}' ")
        data = cursor.fetchone()
        if data == None:
            print("Wrong Credentials")
            break
        else:
            if data[0] == 1:   # Checking
                while c != 1:  # for the root(admin) user
                    print("    Successfully Logged In. \n"
                          "    You are Administrator :)")
                    c = 1
                print("Select your choice: \n"
                      "    1 -> Add A New Book \n" +
                      "    2 -> Update A book Information \n" +
                      "    3 -> Remove A book \n" +
                      "    4 -> View Details of a book \n" +
                      "    5 -> View All Books \n" +
                      "    6 -> Place an Order \n" +
                      "    7 -> Cancel an Order \n"
                      "    8 -> Return/Replace an Order \n" +
                      "    9 -> Update an Order Address \n" +
                      "   10 -> View All Orders \n" +
                      "   11 -> View Orders of a User(s) \n"
                      "   12 -> View Orders by Date \n" +
                      "   13 -> Add a New User \n" +
                      "   14 -> Update A User's Credentials \n" +
                      "   15 -> Remove A User \n"
                      "   16 -> View all Users \n"
                      "   17 -> View Details of some users \n" +
                      "   18 -> Exit")
                ch = int(input("Enter your choice from (1 to 18): "))
                if ch == 1:
                    books.Add_book()
                elif ch == 2:
                    books.Update_book()
                elif ch == 3:
                    books.Delete_book()
                elif ch == 4:
                    books.View_details()
                elif ch == 5:
                    books.View_all()
                elif ch == 6:
                    orders.Place_ord(a)
                elif ch == 7:
                    orders.Cancel_ord()
                elif ch == 8:
                    orders.Return_replace(a)
                elif ch == 9:
                    orders.Update_ord_addr()
                elif ch == 10:
                    orders.View_all_ords()
                elif ch == 11:
                    orders.View_all_u()
                elif ch == 12:
                    orders.View_ord_dt()
                elif ch == 13:
                    acc_ctrl.Add_new()
                elif ch == 14:
                    acc_ctrl.Update_user()
                elif ch == 15:
                    acc_ctrl.Del_user()
                elif ch == 16:
                    acc_ctrl.All_u()
                elif ch == 17:
                    acc_ctrl.View_user()
                elif ch == 18:
                    end_time = time.time()
                    print("Successfully Logged Out. Your active time was ", end_time - start_time, "seconds")
                    exit(0)
                else:
                    print("Wrong Input")
                login = 1
                do_again = input("Go Back to Main Menu? (y -> Yes, n -> No and Logout) ")
                if do_again in ['y', 'yes', 'Y', 'YES']:
                    Main_menu(a, b, c)
                else:
                    end_time = time.time()
                    print("Process Successfully Done. Logged Out")
                    print("Your active time was ", end_time - start_time, "seconds")
                    exit(0)
            else:
                print("     Successfully Logged In.")
                print("    1-> Place an Order \n"
                      "    2-> Cancel an Order \n"
                      "    3-> Return or Replace an Order \n"
                      "    4-> Update an Order Address \n"
                      "    5-> View all your Orders \n" +
                      "    6-> Exit")
                ch2 = int(input("Enter your choice from (1 to 6): "))
                if ch2 == 1:
                    orders.Place_ord(a)
                elif ch2 == 2:
                    orders.Cancel_ord_u(a)
                elif ch2 == 3:
                    orders.Return_replace(a)
                elif ch2 == 4:
                    orders.Up_ord_au(a)
                elif ch2 == 5:
                    orders.View_au(a)
                elif ch2 == 6:
                    end_time = time.time()
                    print("Successfully Logged Out. Your active time was ", end_time - start_time, "seconds")
                    exit(0)
                else:
                    print("Wrong Input.")
                login = 1
                do_again = input("Go Back to Main Menu? (y -> Yes, n -> No and Logout) ")
                if do_again in ['y', 'yes', 'Y', 'YES']:
                    Main_menu(a, b, c)
                else:
                    end_time = time.time()
                    print("Process Successfully Done. Logged Out")
                    print("Your active time was ", end_time - start_time, "seconds")
                    exit(0)
    log_ag = str(input("Enter login details again? (y -> Yes, n -> No and exit): "))
    if log_ag == 'y' or log_ag == 'Y':
        user_id = Usern()
        user_pass = Userp()
        Main_menu(user_id, user_pass, c)
    else:
        end_time = time.time()
        print("Successfully Logged Out. Your active time was ", end_time - start_time, "seconds")
        exit(0)


#  __ main __
# Calling the main program
print("1 -> Sign Up \n"
      "2 -> Sign In")
sign = int(input("Enter your choice: "))
count = 0

if sign == 1:
    tp = acc_ctrl.Sign_Up()
    print("Restart the software to Login.....:)")
elif sign == 2:

    def Usern():
        input_username = input("  Enter Login ID: ").strip()
        return input_username

    def Userp():
        input_password = input("  Enter Password: ").strip()
        return input_password

    x = Usern()
    y = Userp()
    Main_menu(x, y, count)

else:
    print("Wrong Input")
