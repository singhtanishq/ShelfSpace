# Inbuilt Modules
import smtplib
from string import capwords
from time import sleep
import datetime

# Project Modules
import mysql.connector as mycam
import config


# --------------------------------------------------------------------------------------------------- #
# |                            Below Functions are Common                                           | #
# --------------------------------------------------------------------------------------------------- #

# -----------------------------------------------------------------------
''' This function will allow every user in database to place order for any book if it exists in database.
    User is prompted every time to place another order if he/she wants.
    When user says 'n' or 'no' function are called from other modules to generate invoice and invoice number.'''

def Place_ord(username):
    ord_id_ls = []
    cam = mycam.connect(host='localhost', user='root', passwd='Rinshu@03', database='book_shop')
    cursor = cam.cursor(buffered=True)
    cursor.execute("SET SQL_SAFE_UPDATES = 0")

    def work():
        print()
        book_name = str(input('Enter the name of the book ' + ': ')).lower()
        cursor.execute("SELECT * FROM books WHERE title='{}'".format(book_name))
        data = cursor.fetchone()
        if data == None:
            print('Sorry, No book named', book_name, 'found.')
        else:
            print(f"   Book named , {capwords(book_name)},  found details are as follows:-")
            print("    Author's name:           ", capwords(data[2]) + ' ' + capwords(data[3]))
            print("    Released Year:           ", data[4])
            print("    Number of Pages:         ", data[8])
            print("    Words Per Page (Approx): ", data[9])
            print("    Publication:             ", capwords(data[6]))
            print("    Category of Book:        ", capwords(data[5]))
            print("    Available quantity:      ", data[7])
            print("    Price of the book:       ", data[10])
            choice = str(input("Do you want to order this Book ? "))

            if choice in ['yes', 'Yes', 'YES', 'y', 'Y']:
                quantity = int(input('Enter the QUANTITY you want to order: '))
                print('              Checking Stock, please wait...')
                sleep(2)

                if quantity <= data[7]:    # Checking if pieces specified to be bought are present or not for the specified book.
                    print('              Enough quantity found')
                    print('Please fill up your details below: ')

                    name = str(input('     Enter Name: '))
                    address = str(input('     Enter Address: '))
                    dist = str(input('     Enter District: '))
                    city = str(input('     Enter City: '))
                    stu = str(input('     Enter State/UT: '))
                    pin = int(input("     Enter Pincode: "))
                    country = str(input('     Enter Country: '))
                    phone = int(input('     Enter Phone number: '))

                    # Email Address is fetched from the accounts table. This email address will be used to send email
                    cursor.execute(f"SELECT email FROM accounts where username = '{username}'")
                    email = cursor.fetchone()
                    amount = data[10] * quantity
                    cursor.execute(f"SELECT ID FROM accounts WHERE username = '{username}'")
                    custom_id = cursor.fetchone()
                    print('  Now we came at the final step of the process...')
                    print("             Total Amount to be paid is: ", amount)
                    print("             No Delivery Charges Applicable, i.e. Delivery Free")
                    confirm = str(input('  Are you sure you want to confirm this order? '))

                    if confirm in ['yes', 'Yes', 'YES', 'y', 'Y']:
                        details = [name, address, dist, city, stu, pin, country, phone, custom_id]
                        cursor.execute(
                            f"UPDATE books SET stock_quantity = stock_quantity - {quantity} WHERE title = '{book_name}'")
                        cam.commit()
                        cursor.execute(
                            f"INSERT INTO orders "
                            f"(customer_name, address, district, city, state_ut, pincode, country, e_mail, phone_no, pieces, bookname, "
                            f"user_name, order_type) "
                            f"VALUES ('{name}', '{address}', '{dist}', '{city}', '{stu}', {pin}, '{country}', '{email[0]}', {phone}, {quantity}, "
                            f"'{book_name}', '{username}', 'new')")
                        cam.commit()
                        cursor.execute(
                            f"SELECT ord_no, order_dt FROM orders WHERE customer_name = '{name}' and phone_no = {phone} ORDER BY ord_no DESC")
                        data2 = cursor.fetchone()
                        ord_id_ls.append(data2[0])
                        print("Processing your order....")
                        sleep(2)
                        print()
                        print("               Order Placed Successfully.")
                    else:
                        print('Your order has been discarded')

                else:
                    print('Sorry', data[7], 'pieces are left')
                    print('Thanks for visiting, keep shopping :)')
            elif choice in ['no', 'No', 'NO', 'n', 'N']:
                print('Okay.')
            else:
                print('Invalid Input')

        print()
        ch = str(input("Want to place more orders? (y/n): ")).lower()
        if ch in ['y', 'yes']:
            work()
        else:
            details.append(email[0])
            details.append(username)
            inv = config.Inv_no_gen(username)
            config.Pdf_generate(details, ord_id_ls, inv[0], inv[1])
            print("Thanks for visiting us :)")
            print()
    work()
    return

# -----------------------------------------------------------------------
'''This function will be used only if the order is specified for return/replace or order is cancelled
   For that, message and subject or email is defined in their respective functions.
   Sender's Email Address and Password is given in config module of the project
   An email will be sent to the email address of the user with the details.'''

def Send_email(email, subject, msg):
    try:
        server = smtplib.SMTP('smtp.gmail.com:587')
        server.ehlo()
        server.starttls()
        server.login(config.EMAIL_ADDRESS, config.PASSWORD)
        final_message = 'Subject: {}\n\n{}'.format(subject, msg)
        server.sendmail(config.EMAIL_ADDRESS, email, final_message)
        server.quit()
        print(f"An email with all details is sent to you on your E-mail Address {email}")
    except:
        print("Email failed to send.")
    return

# -----------------------------------------------------------------------
'''This function will allow the user to return or replace the order within 7 days after the delivery date.
   Else a message will be displayed that the order is not eligible for passing the Return/Replace Policy.
   By default, the delivery date is the date 7 days after the date of placing the order'''

def Return_replace(username):
    cam = mycam.connect(host='localhost', user='root', passwd='Rinshu@03', database='book_shop')
    cursor = cam.cursor(buffered=True)
    cursor.execute(f"SELECT ord_no FROM orders WHERE user_name = '{username}'")
    record = cursor.fetchall()
    L = []
    if not record:
        print('No order to return or replace')
    else:
        cursor.execute(
            f"SELECT * from orders where user_name = '{username}' and DATEDIFF(NOW(), order_dt) >= 7 and DATEDIFF(NOW(), order_dt) <= 14 "
            f"ORDER by ord_no DESC")
        data = cursor.fetchall()
        if not data:
            print('None of your order is eligible to return or replace.')
        else:
            print('We have found', len(data), 'orders have been delivered to you')
            print('List of the orders that have been delivered to you are as follows:-')
            for i in data:
                L.append(i[0])
                print('   Book Name      : ', i[11])
                print('   Order Date     : ', i[12])
                print('   Order ID       : ', i[0])
                print('   Customer Name  : ', i[1])
                print(f"   Location       :  {i[2]}, {i[3]}, {i[4]}, {i[5]}, {i[6]}, {i[7]}")
                print('   Email          : ', i[8])
                print('   Phone no       : ', i[9])
                print('   No of Books    : ', i[10])
                print()

            choice = str(input('Do you want to return or replace any of the above orders (y/n) ')).lower()

            def work(c):
                if c == 'y':
                    ID = int(input('Enter the order ID for which you want to return or replace: '))
                    if ID not in L:
                        print('No order ID ', ID, ' matched from the orders that have been delivered to you')
                    else:
                        print('You have chosen order ID: ', ID)
                        print('Few details of your order are as follows: ')
                        print()
                        cursor.execute(f"SELECT * FROM orders WHERE ord_no = {ID}")
                        data2 = cursor.fetchone()
                        print('   Book name: ', data2[11])
                        print('   Quantity: ', data2[10])
                        print('   Order date: ', data2[12])
                        print()
                        print('By SNT.bookshop Return and Replace policies, you have below two options')
                        print('1. Return')
                        print('2. Replace')

                        opt = int(input('Enter the option number that you want to select: '))

                        if opt == 1:
                            print('You have entered under our Return policy')
                            confirm = str(input('Are you sure you want to return this order? (y/n) ')).lower()
                            if confirm in ['y', 'yes']:
                                print('   Processing the Return')
                                msg = f"Your request for returning your order has been accepted. Some details for it are as follows: \n" \
                                      f"Book Name: {capwords(data2[11])} \n" \
                                      f"Order ID: {data2[0]} \n" \
                                      f"Name: {data2[1]} \n" \
                                      f"Address: {data2[2]} \n" \
                                      f"District: {data2[3]} \n" \
                                      f"City: {data2[4]} \n" \
                                      f"State: {data2[5]} \n" \
                                      f"Pincode: {data2[6]} \n" \
                                      f"Country: {data2[7]} \n" \
                                      f"Phone: {data2[9]} \n" \
                                      f"Pieces Ordered: {data2[10]} \n" \
                                      f"Order Date & Time: {data2[12]} \n"
                                sub = f"Information of Returning Order on S & T Bookshop"
                                Send_email(data2[8], sub, msg)  # Calling Function to send email
                                # Real Email is sent here.
                                # Email is sent actually to the mailbox if the given email really exists
                                cursor.execute(
                                    f"INSERT INTO orders "
                                    f"(customer_name, address, district, city, state_ut, pincode, country, e_mail, phone_no, pieces, bookname, "
                                    f"user_name, order_type) VALUES ('{data2[1]}', '{data2[2]}', '{data2[3]}', '{data2[4]}', '{data2[5]}', "
                                    f"{data2[6]}, '{data2[7]}', '{data2[8]}', {data2[9]}, {data2[10]}, "
                                    f"'{data2[11]}', '{username}', 'return')")
                                cam.commit()
                                cursor.execute(f"DELETE FROM orders WHERE ord_no = {ID}")
                                cam.commit()
                                print('   Successfully requested for return to your order.')
                                print(
                                    '   Our courier boy will come within the next day to collect the package after verifying its condition, '
                                    '   be ready with the packed book')
                                print('   Money will be refund to your account within 2-3 days')
                                return
                            else:
                                print('   Return process cancelled')

                        elif opt == 2:
                            print('You have entered under our Replace policy.')
                            confirm = str(input('Are you sure you want to replace for this order? (y/n) ')).lower()

                            if confirm in ['y', 'yes']:
                                msg = f"Your request for replacing your order has been accepted. Some details for it are as follows: \n" \
                                      f"Book Name: {capwords(data2[11])} \n" \
                                      f"Order ID: {data2[0]} \n" \
                                      f"Name: {data2[1]} \n" \
                                      f"Address: {data2[2]} \n" \
                                      f"District: {data2[3]} \n" \
                                      f"City: {data2[4]} \n" \
                                      f"State: {data2[5]} \n" \
                                      f"Pincode: {data2[6]} \n" \
                                      f"Country: {data2[7]} \n" \
                                      f"Phone: {data2[9]} \n" \
                                      f"Pieces Ordered: {data2[10]} \n" \
                                      f"Order Date & Time: {data2[12]} \n" \
                                      f"Delivery will be provided within 7 working days. \n" \
                                      f"Sorry for the inconvenience :)"
                                sub = f"Information of Replacing Order on S & T Bookshop"
                                print("   Successfully requested for replacement of your order.")
                                Send_email(data2[8], sub, msg)  # Calling Function to send email
                                # Real Email is sent here.
                                # Email is sent actually to the mailbox if the given email really exists
                                cursor.execute(
                                    f"INSERT INTO orders "
                                    f"(customer_name, address, district, city, state_ut, pincode, country, e_mail, phone_no, pieces, bookname, "
                                    f"user_name, order_type) VALUES ('{data2[1]}', '{data2[2]}', '{data2[3]}', '{data2[4]}', '{data2[5]}', {data2[6]}, "
                                    f"'{data2[7]}', '{data2[8]}', {data2[9]}, {data2[10]}, "
                                    f"'{data2[11]}', '{username}', 'replace')")
                                cam.commit()
                                cursor.execute(f"DELETE FROM orders WHERE ord_no = {ID}")
                                cam.commit()
                                print(
                                    '   Our courier boy will come within the next day to collect the package after verifying its condition, '
                                    '   be ready with the packed book')
                                print(
                                    "   Replacement will be completed within 7 working days until your order has been delivered. ")
                            elif confirm in ['n', 'no']:
                                print("Replacement Cancelled")
                                print("Exiting")
                                return
                        else:
                            print('Invalid option choosen.')
                elif c in ['n', 'no']:
                    print("Exiting")
                    return
                else:
                    print("Wrong Input")
                    again_t = str(input("Do you want to return or replace any of the above orders? (y/n) ")).lower()
                    if again_t in ['yes', 'y']:
                        work(again_t)
                    elif again_t in ['n', 'no']:
                        print("Exiting")
                        return
                    else:
                        print("Invalid Input.")

            work(choice)
    cam.close()
    return

# --------------------------------------------------------------------------------------------------- #
# |                            Below Functions are for Administrator                                |
# --------------------------------------------------------------------------------------------------- #

# -----------------------------------------------------------------------
'''This function will allow the administrator to cancel as many orders he wants by specifying the Order ID
   An email will be sent to the user with details. Order can be cancelled only within 7 days after placing order'''

def Cancel_ord():  # Admin can cancel any user's order
    cam = mycam.connect(host='localhost', user='root', passwd='Rinshu@03', database='book_shop')
    cursor = cam.cursor(buffered=True)
    cursor.execute("SELECT ord_no FROM orders WHERE DATEDIFF(NOW(), order_dt) <= 7")
    rec = cursor.fetchall()
    if len(rec) == 0:
        print("No orders to cancel.")
        print("Sorry")
    else:
        print(f"Only {len(rec)} order(s) is/are eligible to cancel.")
        num = int(input(f"Enter number of orders you want to cancel (not more than {len(rec)}): "))
        if num <= len(rec):
            for i in range(num):
                order_id = int(input('  Enter the Order ID: '))
                cursor.execute(f"SELECT ord_no FROM orders WHERE DATEDIFF(NOW(), order_dt) <= 7 AND ord_no = {order_id}")
                data3 = cursor.fetchone()
                if len(data3) == 1:
                    cursor.execute(f"SELECT * FROM orders WHERE ord_no = {order_id}")
                    data = cursor.fetchone()
                    if data == None:
                        print(f"Order ID {order_id} does not exist.")
                    else:
                        cursor.execute("SET SQL_SAFE_UPDATES = 0")
                        cursor.execute(
                            f"UPDATE books SET stock_quantity = stock_quantity + {data[10]} WHERE title = '{data[11]}'")
                        cam.commit()
                        cursor.execute(f"SELECT publication, author_fname, author_lname FROM books WHERE title = '{data[11]}'")
                        data2 = cursor.fetchone()
                        msg = f"Your Order has been cancelled as per your request. Please review the product on our website. \n" \
                              f"Book Name: {capwords(data[11])} \n" \
                              f"Publication: {capwords(data2[0])} \n" \
                              f"Author's Name: {capwords(data2[1])} {capwords(data2[2])} \n" \
                              f"Order ID: {data[0]} \n" \
                              f"Name: {capwords(data[1])} \n" \
                              f"Address: {data[2]} \n" \
                              f"District: {data[3]} \n" \
                              f"City: {data[4]} \n" \
                              f"State: {data[5]} \n" \
                              f"Pincode: {data[6]} \n" \
                              f"Country: {data[7]} \n" \
                              f"Phone: {data[9]} \n" \
                              f"Pieces Ordered: {data[10]} \n" \
                              f"Order Date & Time: {data[12]}"
                        email = data[8]
                        sub = 'Regarding Cancellation of Order on S & T Bookshop'
                        Send_email(email, sub, msg)
                        cursor.execute(f"DELETE FROM orders WHERE ord_no = {order_id}")
                        cam.commit()
                        print("Successfully cancelled your order.")
                else:
                    print("Order not eligible to cancel.")
        else:
            print(f"Not possible to cancel more than {len(rec)} orders.")
            Cancel_ord()
    cam.close()
    return

# -----------------------------------------------------------------------
'''This function will allow administrator to update the order address of multiple orders'''

def Update_ord_addr():  # Admin can update any user's order
    cam = mycam.connect(host='localhost', user='root', passwd='Rinshu@03', database='book_shop')
    cursor = cam.cursor(buffered=True)
    cursor.execute("SELECT * FROM orders WHERE DATEDIFF(NOW(), order_dt) <= 7")
    lim = cursor.fetchall()
    if not lim:
        print("No orders are eligible for update of address.")
    else:
        print(f"Only {len(lim)} order(s) is/are eligible for update of address.")

        def work(data):
            num = int(input('Enter the number of orders\'s addresses you want to update: '))
            lst = [(data[i][0]) for i in range(len(data))]
            if num <= len(data):
                for i in range(num):
                    order_id = int(input('Enter the Order ID to update the order: '))
                    if order_id in lst:
                        new_addr = str(input('     Enter the new address for order ID ' + str(order_id) + ': '))
                        new_city = str(input('     Enter the new city for order ID    ' + str(order_id) + ': '))
                        new_pinc = int(input('     Enter the new pincode for order ID ' + str(order_id) + ': '))
                        new_dist = str(input('     Enter the new district for Order ID' + str(order_id) + ': '))
                        new_stat = str(input('     Enter the new State/UT for Order ID' + str(order_id) + ': '))
                        cursor.execute("SET SQL_SAFE_UPDATES = 0")
                        cursor.execute("UPDATE orders SET address = '{}' WHERE ord_no = {}".format(new_addr, order_id))
                        cam.commit()
                        cursor.execute("UPDATE orders SET city = '{}'  WHERE ord_no = {}".format(new_city, order_id))
                        cam.commit()
                        cursor.execute("UPDATE orders SET pincode = {}  WHERE ord_no = {}".format(new_pinc, order_id))
                        cam.commit()
                        cursor.execute("UPDATE orders SET district = '{}'  WHERE ord_no = {}".format(new_dist, order_id))
                        cam.commit()
                        cursor.execute("UPDATE orders SET state_ut = '{}'  WHERE ord_no = {}".format(new_stat, order_id))
                        cam.commit()
                        cursor.execute(f"SELECT e_mail FROM orders WHERE ord_no = {order_id}")
                        email = cursor.fetchone()
                        msg = f"Your Order has been updated successfully \n. " \
                              f"New Location of the order is {new_addr}, {new_city}, {new_pinc}, {new_city}, {new_stat} :)"
                        sub = "Information of Order Update on S & T Book Shop Management System"
                        Send_email(email[0], sub, msg)
                        print('Successfully Updated')
                        print(f"regarding order update for new location on email address {email[0]}")
                    else:
                        print("This order ID is not eligible for update of order address.")
                        continue
            else:
                print("Invalid Input. Try Again")
                work(data)
        work(lim)
    cam.close()
    return

# -----------------------------------------------------------------------
'''This function will allow administrator to view all orders in database of every user.'''

def View_all_ords():  # Admin can view all user's order
    cam = mycam.connect(host='localhost', user='root', passwd='Rinshu@03', database='book_shop')
    cursor = cam.cursor(buffered=True)
    print("  1 -> View all New Orders Placed \n"
          "  2 -> View all Orders for Return \n"
          "  3 -> View all Orders for Replacement \n"
          "  4 -> View all Orders including all categories")
    ch = int(input("  Enter your choice (1 to 4): "))

    def start(choice):
        if choice == 1:
            cursor.execute("SELECT * FROM orders WHERE order_type = 'new' ORDER BY ord_no DESC")
            data1 = cursor.fetchall()
            if not data1:
                print("No orders.")
            else:
                for row in data1:
                    tp = row
                    print("    Order ID       : ", tp[0])
                    print("    Book Name      : ", capwords(tp[11]))
                    print("    Pieces         : ", tp[10])
                    print("    Customer Name  : ", capwords(tp[1]))
                    print("    Address        : ", tp[2])
                    print("    District       : ", tp[3])
                    print("    City           : ", tp[4])
                    print("    State          : ", tp[5])
                    print("    Pincode        : ", tp[6])
                    print("    Country        : ", tp[7])
                    print("    E-mail Address : ", tp[8])
                    print("    Phone          : ", tp[9])
                    print("    Order Date     : ", tp[12])
                    print("    Username       : ", tp[13])
                    print()
        elif choice == 2:
            cursor.execute("SELECT * FROM orders WHERE order_type = 'return' ORDER BY ord_no DESC")
            data2 = cursor.fetchall()
            if not data2:
                print("No orders.")
            else:
                for row in data2:
                    tp = row
                    print("    Order ID       : ", tp[0])
                    print("    Book Name      : ", capwords(tp[11]))
                    print("    Pieces         : ", tp[10])
                    print("    Customer Name  : ", capwords(tp[1]))
                    print("    Address        : ", tp[2])
                    print("    District       : ", tp[3])
                    print("    City           : ", tp[4])
                    print("    State          : ", tp[5])
                    print("    Pincode        : ", tp[6])
                    print("    Country        : ", tp[7])
                    print("    E-mail Address : ", tp[8])
                    print("    Phone          : ", tp[9])
                    print("    Order Date     : ", tp[12])
                    print("    Username       : ", tp[13])
                    print()
        elif choice == 3:
            cursor.execute("SELECT * FROM orders WHERE order_type = 'replace' ORDER BY ord_no DESC")
            data1 = cursor.fetchall()
            if not data1:
                print("No orders.")
            else:
                for row in data1:
                    tp = row
                    print("    Order ID       : ", tp[0])
                    print("    Book Name      : ", capwords(tp[11]))
                    print("    Pieces         : ", tp[10])
                    print("    Customer Name  : ", capwords(tp[1]))
                    print("    Address        : ", tp[2])
                    print("    District       : ", tp[3])
                    print("    City           : ", tp[4])
                    print("    State          : ", tp[5])
                    print("    Pincode        : ", tp[6])
                    print("    Country        : ", tp[7])
                    print("    E-mail Address : ", tp[8])
                    print("    Phone          : ", tp[9])
                    print("    Order Date     : ", tp[12])
                    print("    Username       : ", tp[13])
                    print()
        elif choice == 4:
            cursor.execute("SELECT * FROM orders ORDER BY ord_no DESC")
            data = cursor.fetchall()
            if not data:
                print("No orders.")
            else:
                for row in data:
                    tp = row
                    print("    Order ID       : ", tp[0])
                    print("    Book Name      : ", capwords(tp[11]))
                    print("    Pieces         : ", tp[10])
                    print("    Customer Name  : ", capwords(tp[1]))
                    print("    Address        : ", tp[2])
                    print("    District       : ", tp[3])
                    print("    City           : ", tp[4])
                    print("    State          : ", tp[5])
                    print("    Pincode        : ", tp[6])
                    print("    Country        : ", tp[7])
                    print("    E-mail Address : ", tp[8])
                    print("    Phone          : ", tp[9])
                    print("    Order Date     : ", tp[12])
                    print("    Username       : ", tp[13])
                    print("    Order Type     : ", tp[14])
                    if tp[14] not in ['return', 'replace']:
                        cursor.execute(
                            f"SELECT DATE(order_dt) FROM orders WHERE DATEDIFF(NOW(), order_dt) <= 7 AND ord_no = {tp[0]}")
                        data2 = cursor.fetchone()
                        if not data2:
                            cursor.execute(
                                f"SELECT DATE(DATE_ADD(order_dt, INTERVAL 7 DAY)) FROM orders WHERE ord_no = {tp[0]}")
                            data3 = cursor.fetchone()
                            print(f"    Order Status   :  Delivered on {data3[0]}")
                        else:
                            print("    Order Status   :  In transit")
                    print()
        else:
            ch2 = int(input("Wrong Input. Enter Again: "))
            start(ch2)

    start(ch)
    cam.close()
    return

# -----------------------------------------------------------------------
'''This function will allow administrator to view all orders of a user'''

def View_all_u():  # Admin can view any user's order particularly
    cam = mycam.connect(host='localhost', user='root', passwd='Rinshu@03', database='book_shop')
    cursor = cam.cursor(buffered=True)
    cursor.execute("SELECT ord_no FROM orders")
    data = cursor.fetchall()
    if not data:
        print("No orders in database.")
    else:
        user = str(input("Enter the customer's username: "))
        cursor.execute(f"SELECT * FROM orders WHERE user_name = '{user}' ORDER BY order_dt DESC")
        data2 = cursor.fetchall()
        if data2 == None:
            print(f"No orders of username '{user}'.")
        else:
            for row in data2:
                tp = row
                print("    Order ID       : ", tp[0])
                print("    Book Name      : ", capwords(tp[11]))
                print("    Pieces         : ", tp[10])
                print("    Customer Name  : ", capwords(tp[1]))
                print("    Address        : ", tp[2])
                print("    District       : ", tp[3])
                print("    City           : ", tp[4])
                print("    State          : ", tp[5])
                print("    Pincode        : ", tp[6])
                print("    Country        : ", tp[7])
                print("    E-mail Address : ", tp[8])
                print("    Phone          : ", tp[9])
                print("    Order Date     : ", tp[12])
                print("    Order Type     : ", capwords(tp[14]))
                if tp[14] not in ['return', 'replace']:
                    cursor.execute(
                        f"SELECT DATE(order_dt) FROM orders WHERE DATEDIFF(NOW(), order_dt) <= 7 AND ord_no = {tp[0]}")
                    data2 = cursor.fetchone()
                    if not data2:
                        cursor.execute(
                            f"SELECT DATE(DATE_ADD(order_dt, INTERVAL 7 DAY)) FROM orders WHERE ord_no = {tp[0]}")
                        data3 = cursor.fetchone()
                        print(f"    Order Status   :  Delivered on {data3[0]}")
                    else:
                        print("    Order Status   :  In transit")
                print()
    cam.close()
    return

# -----------------------------------------------------------------------
'''This function will allow administrator to view all orders of a particular date'''

def View_ord_dt():  # Admin can view any user's order by date
    cam = mycam.connect(host='localhost', user='root', passwd='Rinshu@03', database='book_shop')
    cursor = cam.cursor(buffered=True)
    cursor.execute("SELECT ord_no FROM orders")
    data = cursor.fetchall()
    if not data:
        print("No orders in database.")
    else:
        dt = str(input("Enter date (YYYY-MM-DD): "))
        cursor.execute(f"SELECT * FROM orders WHERE DATE(order_dt) = '{dt}'")
        data = cursor.fetchall()
        for row in data:
            tp = row
            print("    Order ID       : ", tp[0])
            print("    Book Name      : ", capwords(tp[11]))
            print("    Pieces         : ", tp[10])
            print("    Customer Name  : ", capwords(tp[1]))
            print("    Address        : ", tp[2])
            print("    District       : ", tp[3])
            print("    City           : ", tp[4])
            print("    State          : ", tp[5])
            print("    Pincode        : ", tp[6])
            print("    Country        : ", tp[7])
            print("    E-mail Address : ", tp[8])
            print("    Phone          : ", tp[9])
            print("    Order Date     : ", tp[12])
            print("    Username       : ", tp[13])
            print("    Order Type     : ", capwords(tp[14]))
            if tp[14] not in ['return', 'replace']:
                cursor.execute(f"SELECT DATE(order_dt) FROM orders WHERE DATEDIFF(NOW(), order_dt) <= 7 AND ord_no = {tp[0]}")
                data2 = cursor.fetchone()
                if not data2:
                    cursor.execute(f"SELECT DATE(DATE_ADD(order_dt, INTERVAL 7 DAY)) FROM orders WHERE ord_no = {tp[0]}")
                    data3 = cursor.fetchone()
                    print(f"    Order Status   :  Delivered on {data3[0]}")
                else:
                    print("    Order Status   :  In transit")
            print()
    cam.close()
    return
#  -----------------------------------------------------------------------------------------------------------------
# |                                     Below Functions are only for non-admin users                               |
#  -----------------------------------------------------------------------------------------------------------------

# -----------------------------------------------------------------------
'''This function will allow users to cancel their order only if they cancel it within 7 days of the date since
   order is placed. An email will be sent to the user with the details.'''

def Cancel_ord_u(username):
    cam = mycam.connect(host='localhost', user='root', passwd='Rinshu@03', database='book_shop')
    cursor = cam.cursor(buffered=True)
    cursor.execute(
        f"SELECT * from orders where user_name = '{username}' and DATEDIFF(NOW(), order_dt) <= 7 ORDER by ord_no DESC")
    data = cursor.fetchall()
    list1 = []
    if not data:
        print("None of your orders are eligible to cancel. Sorry :)")
    else:
        print("This is the list of your orders which are eligible to cancel: ")
        for row in data:
            tp = row
            list1.append(tp[0])
            print("    Order ID       : ", tp[0])
            print("    Book Name      : ", capwords(tp[11]))
            print("    Pieces         : ", tp[10])
            print("    Customer Name  : ", capwords(tp[1]))
            print("    Address        : ", tp[2])
            print("    District       : ", tp[3])
            print("    City           : ", tp[4])
            print("    State          : ", tp[5])
            print("    Pincode        : ", tp[6])
            print("    Country        : ", tp[7])
            print("    E-mail Address : ", tp[8])
            print("    Phone          : ", tp[9])
            print("    Order Date     : ", tp[12])
            print("    Order Type     : ", tp[14])

            if tp[14] not in ['return', 'replace']:
                cursor.execute(f"SELECT DATE(order_dt) FROM orders WHERE DATEDIFF(NOW(), order_dt) <= 7 AND ord_no = {tp[0]}")
                data2 = cursor.fetchone()
                if not data2:
                    cursor.execute(f"SELECT DATE(DATE_ADD(order_dt, INTERVAL 7 DAY)) FROM orders WHERE ord_no = {tp[0]}")
                    data3 = cursor.fetchone()
                    print(f"    Order Status   :  Delivered on {data3[0]}")
                else:
                    print("    Order Status   :  In transit")
            print()

        def choose():
            choice = int(input("Enter the Order ID to cancel: "))
            return choice

        ch = choose()
        if ch in list1:
            cursor.execute(f"SELECT * FROM orders WHERE ord_no = {ch}")
            data2 = cursor.fetchone()
            cursor.execute(f"SELECT publication, author_fname, author_lname FROM books WHERE title = '{data2[11]}'")
            data3 = cursor.fetchone()
            msg = f"Your Order has been cancelled as per your request. Please review the product on our website. \n\n" \
                  f"Book Name: {capwords(data2[11])} \n" \
                  f"Publication: {capwords(data3[0])} \n" \
                  f"Author's Name: {capwords(data3[1])} {capwords(data3[2])} \n" \
                  f"Order ID: {data2[0]} \n" \
                  f"Name: {capwords(data2[1])} \n" \
                  f"Address: {data2[2]} \n" \
                  f"District: {data2[3]} \n" \
                  f"City: {data2[4]} \n" \
                  f"State: {data2[5]} \n" \
                  f"Pincode: {data2[6]} \n" \
                  f"Country: {data2[7]} \n" \
                  f"Phone: {data2[9]} \n" \
                  f"Pieces Ordered: {data2[10]} \n" \
                  f"Order Date & Time: {data2[12]} \n" \
                  f"Order Status: Cancelled on {datetime.datetime.now()}"
            email = data2[8]
            sub = 'Regarding Cancellation of Order on S & T Bookshop'
            Send_email(email, sub, msg)
            cursor.execute("SET SQL_SAFE_UPDATES = 0")
            cursor.execute(
                f"UPDATE books SET stock_quantity = stock_quantity + {data2[10]} WHERE title = '{data2[11]}'")
            cam.commit()
            cursor.execute(f"DELETE FROM orders where ord_no = {ch}")
            cam.commit()
            print("Successfully Cancelled the Order.")
        if len(list1) > 1:
            ch2 = str(input("   Want to cancel more Orders? (y OR n) "))
            if ch2 == 'y' or ch2 == 'Y':
                Cancel_ord_u(username)
            elif ch2 == 'n' or ch2 == 'N':
                cam.close()
                return
            else:
                print("Wrong Input")
                return
        else:
            pass

# -----------------------------------------------------------------------
'''This function will allow administrator to update his/her order address if they do it within 7 days after
   order is being placed. An email will be sent with few order details and new location of delivery.'''

def Up_ord_au(username):
    cam = mycam.connect(host='localhost', user='root', passwd='Rinshu@03', database='book_shop')
    cursor = cam.cursor(buffered=True)
    cursor.execute(f"SELECT * FROM orders WHERE user_name = '{username}' and DATEDIFF(NOW(), order_dt) <= 7 ORDER BY ord_no DESC")
    data = cursor.fetchall()
    list1 = []
    if data == None:
        print("No 'IN TRANSIT' orders in database for your username.")
    else:
        print("This is the list of your orders eligible for updating the address: ")
        for row in data:
            tp = row
            list1.append(tp[0])
            print("    Order ID:       ", tp[0])
            print("    Book Name:      ", capwords(tp[11]))
            print("    Pieces:         ", tp[10])
            print("    Customer Name:  ", capwords(tp[1]))
            print("    Address:        ", tp[2])
            print("    District:       ", tp[3])
            print("    City:           ", tp[4])
            print("    State/UT:       ", tp[5])
            print("    Pincode:        ", tp[6])
            print("    Country:        ", tp[7])
            print("    E-mail Address: ", tp[8])
            print("    Phone:          ", tp[9])
            print("    Order Date:     ", tp[12])
            print()

        def choose():
            choice = int(input("Enter the Order ID to update address: "))
            return choice
        ch = choose()
        if ch in list1:
            new_addr = str(input("Enter the new address: "))
            new_city = str(input("Enter City: "))
            new_pinc = int(input('Enter pincode: '))
            new_dist = str(input("Enter District: "))
            new_stat = str(input("Enter State/UT" + ': '))
            cursor.execute("SET SQL_SAFE_UPDATES = 0")
            cursor.execute(f"UPDATE orders SET address = '{new_addr}' WHERE ord_no = {ch}")
            cam.commit()
            cursor.execute(f"UPDATE orders SET city = '{new_city}' WHERE ord_no = '{ch}'")
            cam.commit()
            cursor.execute(f"UPDATE orders SET pincode = {new_pinc}  WHERE ord_no = {ch}")
            cam.commit()
            cursor.execute(f"UPDATE orders SET district = '{new_dist}' WHERE ord_no = '{ch}'")
            cam.commit()
            cursor.execute(f"UPDATE orders SET state_ut = '{new_stat}' WHERE ord_no = '{ch}'")
            cam.commit()
            print('Successfully Updated')
            cursor.execute(f"SELECT email FROM accounts WHERE username = '{username}'")
            email = cursor.fetchone()
            msg = f"Your Order has been updated successfully. \n" \
                  f"New Location of the order is {new_addr}, {new_city}, {new_pinc}, {new_city}, {new_stat} :)"
            sub = "Information of Order Update on S & T Book Shop Management System"
            Send_email(email[0], sub, msg)
            print()

        if len(list1) > 1:
            ch2 = str(input("   Want to update more Orders? (y OR n): "))
            if ch2 == 'y' or ch2 == 'Y':
                Up_ord_au(username)
            elif ch2 == 'n' or ch2 == 'N':
                return
            else:
                print("Wrong Input")
                return
        else:
            pass
    cam.close()
    return

#  -----------------------------------------------------------------------
'''This function will allow the signed in user to view all their details of every order placed since 
   registered with detail of order type (i.e, new or for replace or for return)'''

def View_au(username):
    cam = mycam.connect(host='localhost', user='root', passwd='Rinshu@03', database='book_shop')
    cursor = cam.cursor(buffered=True)
    print("This is the list of your orders.: ")
    cursor.execute(f"SELECT * FROM orders WHERE user_name = '{username}' ORDER BY ord_no DESC")
    data = cursor.fetchall()
    if data == None:
        print("No orders in database.")
    else:
        print("                   Latest Orders Sorted by Date:. ")
        for row in data:
            tp = row
            print("    Order ID       : ", tp[0])
            print("    Book Name      : ", capwords(tp[11]))
            print("    Pieces         : ", tp[10])
            print("    Customer Name  : ", capwords(tp[1]))
            print("    Address        : ", tp[2])
            print("    District       : ", tp[3])
            print("    City           : ", tp[4])
            print("    State/UT       : ", tp[5])
            print("    Pincode        : ", tp[6])
            print("    Country        : ", tp[7])
            print("    E-mail Address : ", tp[8])
            print("    Phone          : ", tp[9])
            print("    Order Date     : ", tp[12])
            print("    Order Type     : ", capwords(tp[14]))

            if tp[14] not in ['return', 'replace']:
                cursor.execute(f"SELECT DATE(order_dt) FROM orders WHERE DATEDIFF(NOW(), order_dt) <= 7 AND ord_no = {tp[0]}")
                data2 = cursor.fetchone()
                if not data2:
                    cursor.execute(f"SELECT DATE(DATE_ADD(order_dt, INTERVAL 7 DAY)) FROM orders WHERE ord_no = {tp[0]}")
                    data3 = cursor.fetchone()
                    print(f"    Order Status   :  Delivered on {data3[0]}")
                else:
                    print("    Order Status   :  In transit")
            print()
    cam.close()
    return

# ---------------------------------------------------------------------------------------------------
# |                                         End of Module                                           |
# # -------------------------------------------------------------------------------------------------
