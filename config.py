import mysql.connector as mycam2
from fpdf import FPDF
from pdf_mail import sendpdf
from datetime import date
from string import capwords
# ----------------------------------------------------------------------
'''Below EMAIL_ADDRESS and PASSWORD is for sending email(s) to users (constant values)'''

EMAIL_ADDRESS = 'snt.bookshop@gmail.com'
PASSWORD = 'S&T@bookshp@341'

# ----------------------------------------------------------------------
'''This function is defined to send invoice of the order placed by any user
   which will fetch the given PDF INVOICE from the specific path where all invoices generated are saved.
   Module used here is 'pdf_mail' '''

def Pdf_mailing(file_name, address):
    sender_email_address = EMAIL_ADDRESS
    receiver_email_address = f"{address}"
    sender_email_password = PASSWORD
    subject_of_email = "Information of Order Placed on S & T Book Shop"
    body_of_email = "This is an auto generated bill of supply for your ordered book(s). \nIf any error is there, please reply to us " \
                    "on our E-mail Address snt.bookshop@gmail.com." \
                    "Thanks for shopping. :)"
    filename = file_name
    location_of_file = "D:/Swarit/Class 12/Class 12 Computer Project/invoices"
    k = sendpdf(sender_email_address, receiver_email_address,
                sender_email_password,
                subject_of_email,
                body_of_email,
                filename, location_of_file)
    k.email_send()


# -----------------------------------------------------------------------
'''This function do two works. First, it makes a string sum of ASCII values of the username of the user
   Second it trims the string generated to length of 10 characters, query of the numbers of orders placed 
   by the user since registered and store it in another string which is displayed in invoice number field
   of invoice generated on placing order.
   Module used here is 'mysql.connector'. '''

def Inv_no_gen(a):
    cam = mycam2.connect(host='localhost', user='root', passwd='Rinshu@03', database='book_shop')
    cursor = cam.cursor()
    st = ''
    st2 = ''
    for char in a:
        x = ord(char)
        st += str(x)  # String sum of ASCII characters of username passed into function generated in st

    # Underneath 'for' loop is defined to limit the number of characters of the username to 10 so that
    # when invoice number will be displayed in the invoice it doesn't go out of the cell defined for it.
    # This is stored in 'st2'
    if len(st) <= 10:
        st2 += st
    else:
        for i in range(0, 10):
            st2 += st[i]
            
            # This query is done so as to get the total number of orders placed since the user has registered
    cursor.execute(f"SELECT count(ord_no) FROM orders WHERE user_name = '{a}'")
    ord_count = cursor.fetchone()
    # We are adding the result of the above query to above generated 'st2' and adding 1 to it
    # so that the invoice number generated is unique every time and no invoice gets replaced
    # due to same name
    st2 += f'{ord_count[0] + 1}'
    return st, st2


# -----------------------------------------------------------------------
'''This function generates PDF invoice with all the details of the user and the 
   book shop and save it on local desktop. User is asked whether he/she wants to get invoice on his/her
   email-address or not. Invoice will be sent to the user's email address only if the user says 'y'.
   Invoice name is string sum of all the ASCII values of the characters of username of the user and the last digit
   will be one more than the number of all orders placed since the user has registered himself/herself.
   This is done so that the invoice generated last time do not get replaced upon new order placed on local desktop.
   Modules used here are 'fpdf' and 'mysql.connector'.'''

def Pdf_generate(ls1, ls2, inv, inv_no):
    lst_sum = []
    cam = mycam2.connect(host='localhost', user='root', passwd='Rinshu@03', database='book_shop')
    cursor = cam.cursor()
    cursor.execute(f"SELECT count(ord_no) FROM orders WHERE user_name = '{ls1[10]}'")
    ord_count = cursor.fetchone()
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Arial", 'B', size=15)

    pdf.cell(130, 5, 'S & T BOOKSHOP', 0, 0, 'L')
    pdf.cell(60, 5, 'Bill of Supply/ Invoice', 0, 1, 'C')

    pdf.set_font("Arial", '', size=12)

    pdf.cell(130, 5, 'Street Address: K-61/74, Sector 8, Pandeypur', 0, 0, 'L')
    pdf.cell(60, 5, '', 0, 1, 'L')

    pdf.cell(130, 5, 'Varanasi, India, ZIP-221002', 0, 0, 'L')
    pdf.cell(25, 5, 'Date: ', 0, 0, 'L')
    pdf.cell(34, 5, f'{date.today()}', 0, 1, 'L')

    pdf.cell(130, 5, 'Phone: (+91)8004125336', 0, 0, 'L')
    pdf.cell(25, 5, 'Invoice #', 0, 0, 'L')
    pdf.cell(34, 5, f"{inv_no}", 0, 1, 'L')

    pdf.cell(130, 5, 'Fax: [+ 91 542 14512]', 0, 0, 'L')
    pdf.cell(25, 5, 'Customer ID', 0, 0, 'L')
    pdf.cell(34, 5, f'{ls1[8][0]}', 0, 1, 'L')

    pdf.cell(130, 5, 'GSTIN: 22AABCU9603R1ZX', 0, 1, 'L')

    pdf.cell(189, 10, '', 0, 1, 'L')

    pdf.set_font("Arial", 'B', size=15)

    pdf.cell(100, 5, 'Billing Address / Shipping Address: ', 0, 1)

    pdf.set_font('Arial', '', size=12)

    pdf.cell(10, 5, '', 0, 0)
    pdf.cell(90, 5, f'{ls1[0]}', 0, 1)  # Name

    pdf.cell(10, 5, '', 0, 0)
    pdf.cell(90, 5, f'{ls1[1]}, {ls1[3]}', 0, 1)  # Address 1

    pdf.cell(10, 5, '', 0, 0)
    pdf.cell(90, 5, f'{ls1[2]}, {ls1[4]}', 0, 1)  # Address 2

    pdf.cell(10, 5, '', 0, 0)
    pdf.cell(90, 5, f'{ls1[5]}, {ls1[6]}', 0, 1)  # Pincode

    pdf.cell(10, 5, '', 0, 0)
    pdf.cell(90, 5, f'Phone: {ls1[7]}', 0, 1)  # Phone

    pdf.cell(189, 10, '', 0, 1, 'L')

    pdf.set_font('Arial', 'B', size=12)

    pdf.cell(10, 5, 'S.no', 1, 0, 'C')
    pdf.cell(100, 5, 'Description', 1, 0, 'C')
    pdf.cell(25, 5, 'Quantity', 1, 0, 'C')
    pdf.cell(25, 5, 'Rate', 1, 0, 'C')
    pdf.cell(30, 5, 'Amount(Rs.)', 1, 1, 'C')

    pdf.set_font('Arial', '', 12)

    # For Loop defined below is to enter the details(quantity, rate, bookname, author's name and amount)
    # into the invoice (i.e.) one invoice will be generated until an unless user exits the function.
    # The last provided address and phone will be written in the billing address of thr invoice

    for i in range(len(ls2)):
        cursor.execute(f"SELECT bookname, pieces FROM orders WHERE ord_no = {ls2[i]}")
        data = cursor.fetchone()
        cursor.execute(f"SELECT author_fname, author_lname, price FROM books WHERE title = '{data[0]}'")
        data2 = cursor.fetchone()
        pdf.cell(10, 5, f"{i + 1}", 1, 0, 'R')
        pdf.cell(100, 5, f'{capwords(data[0])} - {capwords(data2[0])} {capwords(data2[1])}', 1, 0, align='L')
        pdf.cell(25, 5, f'{data[1]}', 1, 0, align='R')
        pdf.cell(25, 5, f'{data2[2]}', 1, 0, align='R')
        pdf.cell(30, 5, f'{data[1] * data2[2]}', 1, 1, align='R')
        lst_sum.append(data[1] * data2[2])
    # Here total of all the books ordered will be calculated
    total = 0
    for num in lst_sum:
        total += num

    pdf.cell(10, 5, '', 0, 0)
    pdf.cell(100, 5, '', 0, 0)
    pdf.cell(25, 5, '', 0, 0)

    pdf.set_font('Arial', 'B', size=12)

    pdf.cell(25, 5, 'Total', 1, 0, 'C')

    pdf.set_font('Arial', 'B', size=12)
    # Total calculated above will be displayed here
    pdf.cell(30, 5, f'{total}', 1, 1, 'R')

    file_n = f"invoice{inv}{ord_count[0] + 1} "
    path = f"D:/Swarit/Class 12/Class 12 Computer Project/invoices/{file_n}.pdf"
    pdf.output(f"{path}")  # Invoice generated and saved to local desktop

    choice = str(input("    Do you want the invoice to be sent to your email address? (y/n): ")).lower()
    if choice in ['y', 'yes']:
        Pdf_mailing(file_n, address=ls1[9])
        print(f"An email has been sent to you with an invoice to your email address {ls1[9]}")
    else:
        pass
# ---------------------------------------------------------------------------------------------------
# |                                         End of Module                                           |
# ---------------------------------------------------------------------------------------------------
