import sys
import sqlite3
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QFormLayout, QLabel, QLineEdit, 
                             QPushButton, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView, QDateEdit, QInputDialog)
from PyQt5.QtCore import QDate
from fpdf import FPDF
from custom import CustomPDF

# Database setup
conn = sqlite3.connect('invoices.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS invoices
             (invoice_id INTEGER PRIMARY KEY AUTOINCREMENT,
              date TEXT,
              venue TEXT,
              customer_name TEXT,
              customer_phone TEXT,
              total_amount REAL,
              paid_amount REAL,
              remaining_amount REAL,
              paid_status TEXT)''')
# conn.commit()


c.execute('''CREATE TABLE IF NOT EXISTS invoice_items
             (item_id INTEGER PRIMARY KEY AUTOINCREMENT,
              invoice_id INTEGER,
              name TEXT,
              description TEXT,
              price REAL,
              quantity INTEGER,
              total_price REAL,
              FOREIGN KEY(invoice_id) REFERENCES invoices(invoice_id))''')
conn.commit()

class InvoiceGenerator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Invoice Generator')
        self.setGeometry(100, 100, 800, 600)
        
        self.centralWidget = QWidget()
        self.setCentralWidget(self.centralWidget)
        
        self.layout = QVBoxLayout()
        
        # Form Layout
        self.formLayout = QFormLayout()
        
        self.dateInput = QDateEdit(self)
        self.dateInput.setCalendarPopup(True)
        self.dateInput.setDate(QDate.currentDate())
        
        self.venueInput = QLineEdit(self)
        self.customerInput = QLineEdit(self)
        self.phoneInput = QLineEdit(self)
        self.paidAmountInput = QLineEdit(self)
        self.remainingAmountLabel = QLabel('Remaining Amount: 0.0', self)
        self.paidStatusLabel = QLabel('Paid Status: Not Paid', self)
        
        self.formLayout.addRow('Date:', self.dateInput)
        self.formLayout.addRow('Venue:', self.venueInput)
        self.formLayout.addRow('Customer Name:', self.customerInput)
        self.formLayout.addRow('Customer Phone:', self.phoneInput)
        self.formLayout.addRow('Paid Amount:', self.paidAmountInput)
        self.formLayout.addRow(self.remainingAmountLabel)
        self.formLayout.addRow(self.paidStatusLabel)
        
        self.layout.addLayout(self.formLayout)
        
        # Item Entry Layout
        self.itemEntryLayout = QFormLayout()
        
        self.itemNameInput = QLineEdit(self)
        self.itemDescriptionInput = QLineEdit(self)
        self.itemPriceInput = QLineEdit(self)
        self.itemQuantityInput = QLineEdit(self)
        
        self.itemEntryLayout.addRow('Item Name:', self.itemNameInput)
        self.itemEntryLayout.addRow('Description:', self.itemDescriptionInput)
        self.itemEntryLayout.addRow('Price:', self.itemPriceInput)
        self.itemEntryLayout.addRow('Quantity:', self.itemQuantityInput)
        
        self.layout.addLayout(self.itemEntryLayout)
        
        self.addItemButton = QPushButton('Add Item', self)
        self.addItemButton.clicked.connect(self.add_item)
        
        self.layout.addWidget(self.addItemButton)
        
        # Table for items
        self.itemsTable = QTableWidget(0, 5)
        self.itemsTable.setHorizontalHeaderLabels(['Name', 'Description', 'Price', 'Quantity', 'Total Price'])
        self.itemsTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        self.layout.addWidget(self.itemsTable)
        
        # Total Amount
        self.totalAmountLabel = QLabel('Total Amount: 0.0', self)
        self.layout.addWidget(self.totalAmountLabel)
        
        # Buttons
        self.saveButton = QPushButton('Save Invoice', self)
        self.viewButton = QPushButton('View Invoices', self)
        
        self.saveButton.clicked.connect(self.save_and_generate_pdf)
        self.viewButton.clicked.connect(self.view_invoices)
        
        self.layout.addWidget(self.saveButton)
        self.layout.addWidget(self.viewButton)
        
        self.centralWidget.setLayout(self.layout)

    def add_item(self):
        name = self.itemNameInput.text()
        description = self.itemDescriptionInput.text()
        price = self.itemPriceInput.text()
        quantity = self.itemQuantityInput.text()
        
        try:
            price = float(price)
            quantity = int(quantity)
            total_price = price * quantity
            
            rowPosition = self.itemsTable.rowCount()
            self.itemsTable.insertRow(rowPosition)
            self.itemsTable.setItem(rowPosition, 0, QTableWidgetItem(name))
            self.itemsTable.setItem(rowPosition, 1, QTableWidgetItem(description))
            self.itemsTable.setItem(rowPosition, 2, QTableWidgetItem(f'{price:.2f}'))
            self.itemsTable.setItem(rowPosition, 3, QTableWidgetItem(f'{quantity}'))
            self.itemsTable.setItem(rowPosition, 4, QTableWidgetItem(f'{total_price:.2f}'))
            
            self.update_total_amount()
            self.clear_item_fields()
        except ValueError:
            QMessageBox.warning(self, 'Error', 'Please enter valid price and quantity.')

    def clear_item_fields(self):
        self.itemNameInput.clear()
        self.itemDescriptionInput.clear()
        self.itemPriceInput.clear()
        self.itemQuantityInput.clear()
        
    def update_total_amount(self):
        total_amount = 0.0
        for row in range(self.itemsTable.rowCount()):
            try:
                total_price = float(self.itemsTable.item(row, 4).text())
                total_amount += total_price
            except (ValueError, TypeError):
                pass
        self.totalAmountLabel.setText(f'Total Amount: {total_amount:.2f}')
        
    def save_and_generate_pdf(self):
        date = self.dateInput.text()
        venue = self.venueInput.text()
        customer_name = self.customerInput.text()
        customer_phone = self.phoneInput.text()
        paid_amount = float(self.paidAmountInput.text())

        total_amount = self.calculate_total_amount()
        remaining_amount = total_amount - paid_amount
        paid_status = "Paid" if remaining_amount == 0 else "Not Paid"

        if date and venue and customer_name and customer_phone and self.itemsTable.rowCount() > 0:
            conn = sqlite3.connect('invoices.db')
            c = conn.cursor()
            c.execute("""INSERT INTO invoices (date, venue, customer_name, customer_phone, total_amount, paid_amount, remaining_amount, paid_status)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                      (date, venue, customer_name, customer_phone, total_amount, paid_amount, remaining_amount, paid_status))
            invoice_id = c.lastrowid

            for row in range(self.itemsTable.rowCount()):
                name = self.itemsTable.item(row, 0).text()
                description = self.itemsTable.item(row, 1).text()
                price = float(self.itemsTable.item(row, 2).text())
                quantity = int(self.itemsTable.item(row, 3).text())
                total_price = float(self.itemsTable.item(row, 4).text())
                c.execute("""INSERT INTO invoice_items (invoice_id, name, description, price, quantity, total_price)
                             VALUES (?, ?, ?, ?, ?, ?)""",
                          (invoice_id, name, description, price, quantity, total_price))

            conn.commit()
            conn.close()
            QMessageBox.information(self, 'Success', 'Invoice saved successfully!')

            # Generate PDF using saved data
            conn = sqlite3.connect('invoices.db')
            c = conn.cursor()

            # Fetch the latest invoice details
            c.execute("SELECT * FROM invoices WHERE invoice_id = ?", (invoice_id,))
            invoice = c.fetchone()

            # Fetch items related to the invoice
            c.execute("SELECT * FROM invoice_items WHERE invoice_id = ?", (invoice_id,))
            items = c.fetchall()

            conn.close()

            # Generate PDF
            pdf = CustomPDF()
            pdf.add_page()

            pdf.set_char_spacing(0)
        
            # Invoice Header
            pdf.set_font("Helvetica", size=15, style='B')
            pdf.set_fill_color(0, 0, 0)
            pdf.set_text_color(255, 255, 255)
            pdf.set_xy(x=0, y=5)
            pdf.cell(210, 10, txt='INVOICE', align='C', fill=True)
            
            # Reset Colors
            pdf.set_fill_color(255, 255, 255)
            pdf.set_text_color(0, 0, 0)
            
            # Set Logo
            pdf.image('logo_resized.png', x=10, y=20, w=50, h=35)
            
            pdf.set_font("Helvetica", size=14, style='B')
            
            # Align right with Logo
            pdf.set_xy(x=120, y=30)
            pdf.set_fill_color(238, 238, 238)
            pdf.cell(30, 7, txt=f"Invoice ID:", ln=True, align='L', fill=True, border=1)
            pdf.set_xy(x=150, y=30)
            pdf.set_font("Helvetica", size=14, style='')
            pdf.cell(40, 7, txt=f"{invoice[0]}", ln=True, align='L', border=1, fill=False)
            pdf.set_xy(x=120, y=37)
            pdf.set_font("Helvetica", size=14, style='B')
            pdf.cell(30, 7, txt=f"Date:", ln=True, align='L', fill=True, border=1)
            pdf.set_xy(x=150, y=37)
            pdf.set_font("Helvetica", size=14, style='')
            pdf.cell(40, 7, txt=f"{invoice[1]}", ln=True, align='L', border=1, fill=False)
            pdf.set_xy(x=120, y=44)
            pdf.set_font("Helvetica", size=14, style='B')
            pdf.multi_cell(30, 7, txt=f"Venue:", ln=True, align='L', fill=True, border=1)
            pdf.set_xy(x=150, y=44)
            pdf.set_font("Helvetica", size=14, style='')
            pdf.multi_cell(40, 7, txt=f"{invoice[2]}", ln=True, align='L', border=1, fill=False)
            
            pdf.set_font("Helvetica", size=10, style='')
            
            # Below Logo Customer Details
            pdf.set_xy(x=7, y=81)
            pdf.cell(43, 7, txt=f"Customer Name:", ln=True, align='L', fill=True, border=1)
            pdf.set_xy(x=48, y=81)
            pdf.cell(43, 7, txt=f"{invoice[3]}", ln=True, align='L', fill=True, border=1)
            pdf.set_xy(x=7, y=88)
            pdf.cell(43, 7, txt=f"Customer Phone:", ln=True, align='L', fill=True, border=1)
            pdf.set_xy(x=48, y=88)
            pdf.cell(43, 7, txt=f"{invoice[4]}", ln=True, align='L', fill=True, border=1)
            # pdf.cell(200, 10, txt=f"Customer Phone: {invoice[4]}", ln=True, align='L')
            # pdf.cell(200, 10, txt=f"Total Amount: {invoice[5]:.2f}", ln=True, align='L')
                    
            # Align right with Customer Details
            pdf.set_xy(x=120, y=81)
            pdf.set_fill_color(238, 238, 238)
            pdf.cell(30, 7, txt=f"Account Title:", ln=True, align='L', fill=True, border=1)
            pdf.set_xy(x=150, y=81)
            pdf.cell(55, 7, txt=f"Rameez Ahmed", ln=True, align='L', border=1, fill=False)
            pdf.set_xy(x=120, y=88)
            pdf.cell(30, 7, txt=f"Account Number:", ln=True, align='L', fill=True, border=1)
            pdf.set_xy(x=150, y=88)
            pdf.cell(55, 7, txt=f"00207901029503", ln=True, align='L', border=1, fill=False)
            pdf.set_xy(x=120, y=95)
            pdf.cell(30, 7, txt=f"IBAN:", ln=True, align='L', fill=True, border=1)
            pdf.set_xy(x=150, y=95)
            pdf.cell(55, 7, txt=f"PK58HABB0000207901029503", ln=True, align='L', border=1, fill=False)
            
            pdf.cell(200, 10, txt="", ln=True, align='L')
            
            pdf.ln()
            
            pdf.set_x(x=5)
            
            pdf.multi_cell_row(5, 40, 10, ["Item Name", "Description", "Price", "Quantity", "Total Price"], to_fill=True)

            pdf.set_font("Helvetica", size=11, style='')

            for item in items:
                pdf.set_x(x=5)
                pdf.multi_cell_row(5, 40, 5, [item[2], item[3], f"{item[4]:.2f}", str(item[5]), f"{item[6]:.2f}"], to_fill=False)
            
            pdf.set_font("Helvetica", size=12)
            
            pdf.set_x(x=5)
            pdf.multi_cell_row(5, 40, 10, ["", "", "", "Total Amount", f"{invoice[5]:.2f}"], to_fill=False)
            pdf.multi_cell_row(5, 40, 10, ["", "", "", "Paid Amount", f"{invoice[6]:.2f}"], to_fill=False)
            pdf.multi_cell_row(5, 40, 10, ["", "", "", "Remaining Amount", f"{invoice[7]:.2f}"], to_fill=False)
            pdf.multi_cell_row(5, 40, 10, ["", "", "", "Paid Status", f"{invoice[8]}"], to_fill=False)
            
            pdf_name = f"invoices/invoice_{invoice_id}.pdf"

            QMessageBox.information(self, 'PDF Generated', f'PDF file has been generated: {pdf_name}')
            self.clear_form()
        else:
            QMessageBox.warning(self, 'Error', 'Please fill all fields.')
    
    def calculate_total_amount(self):
        total_amount = 0.0
        for row in range(self.itemsTable.rowCount()):
            try:
                total_price = float(self.itemsTable.item(row, 4).text())
                total_amount += total_price
            except (ValueError, TypeError):
                pass
        return total_amount
    
    def clear_form(self):
        self.dateInput.setDate(QDate.currentDate())
        self.venueInput.clear()
        self.customerInput.clear()
        self.phoneInput.clear()
        self.paidAmountInput.clear()
        self.itemsTable.setRowCount(0)
        self.totalAmountLabel.setText('Total Amount: 0.0')
        self.remainingAmountLabel.setText('Remaining Amount: 0.0')
        self.paidStatusLabel.setText('Paid Status: Not Paid')
    
    def view_invoices(self):
        password, ok = QInputDialog.getText(self, 'Authentication', 'Enter password:', QLineEdit.Password)
        if ok and password == 'admin':  # Replace 'your_password' with the actual password
            self.invoiceWindow = InvoiceViewer()
            self.invoiceWindow.show()
        else:
            QMessageBox.warning(self, 'Error', 'Authentication failed')


class InvoiceViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('View Invoices')
        self.setGeometry(200, 200, 1000, 600)
        
        self.centralWidget = QWidget()
        self.setCentralWidget(self.centralWidget)
        
        self.layout = QVBoxLayout()
        
        self.tableWidget = QTableWidget()
        self.layout.addWidget(self.tableWidget)
        
        self.centralWidget.setLayout(self.layout)
        
        self.load_invoices()

    def load_invoices(self):
        conn = sqlite3.connect('invoices.db')
        c = conn.cursor()
        c.execute("SELECT * FROM invoices")
        invoices = c.fetchall()
        
        # Update the table widget to include new columns
        self.tableWidget.setRowCount(len(invoices))
        self.tableWidget.setColumnCount(9)
        self.tableWidget.setHorizontalHeaderLabels([
            'Invoice ID', 'Date', 'Venue', 'Customer Name', 
            'Customer Phone', 'Total Amount', 'Paid Amount', 
            'Remaining Amount', 'Paid Status'
        ])
        
        for row_num, row_data in enumerate(invoices):
            for col_num, data in enumerate(row_data):
                self.tableWidget.setItem(row_num, col_num, QTableWidgetItem(str(data)))
        
        conn.close()
        
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # Connect double-click event to the generate_pdf method
        self.tableWidget.itemDoubleClicked.connect(self.generate_pdf)


    def generate_pdf(self, item):
        row = item.row()
        invoice_id = int(self.tableWidget.item(row, 0).text())
        
        conn = sqlite3.connect('invoices.db')
        c = conn.cursor()
        c.execute("SELECT * FROM invoices WHERE invoice_id = ?", (invoice_id,))
        invoice = c.fetchone()
        
        c.execute("SELECT * FROM invoice_items WHERE invoice_id = ?", (invoice_id,))
        items = c.fetchall()
        conn.close()

        pdf = CustomPDF()
        pdf.add_page()
        
        pdf.set_char_spacing(0)
        
        # Invoice Header
        pdf.set_font("Helvetica", size=15, style='B')
        pdf.set_fill_color(0, 0, 0)
        pdf.set_text_color(255, 255, 255)
        pdf.set_xy(x=0, y=5)
        pdf.cell(210, 10, txt='INVOICE', align='C', fill=True)
        
        # Reset Colors
        pdf.set_fill_color(255, 255, 255)
        pdf.set_text_color(0, 0, 0)
        
        # Set Logo
        pdf.image('logo_resized.png', x=10, y=20, w=50, h=35)
        
        pdf.set_font("Helvetica", size=14, style='B')
        
        # Align right with Logo
        pdf.set_xy(x=120, y=30)
        pdf.set_fill_color(238, 238, 238)
        pdf.cell(30, 7, txt=f"Invoice ID:", ln=True, align='L', fill=True, border=1)
        pdf.set_xy(x=150, y=30)
        pdf.set_font("Helvetica", size=14, style='')
        pdf.cell(40, 7, txt=f"{invoice[0]}", ln=True, align='L', border=1, fill=False)
        pdf.set_xy(x=120, y=37)
        pdf.set_font("Helvetica", size=14, style='B')
        pdf.cell(30, 7, txt=f"Date:", ln=True, align='L', fill=True, border=1)
        pdf.set_xy(x=150, y=37)
        pdf.set_font("Helvetica", size=14, style='')
        pdf.cell(40, 7, txt=f"{invoice[1]}", ln=True, align='L', border=1, fill=False)
        pdf.set_xy(x=120, y=44)
        pdf.set_font("Helvetica", size=14, style='B')
        pdf.multi_cell(30, 7, txt=f"Venue:", ln=True, align='L', fill=True, border=1)
        pdf.set_xy(x=150, y=44)
        pdf.set_font("Helvetica", size=14, style='')
        pdf.multi_cell(40, 7, txt=f"{invoice[2]}", ln=True, align='L', border=1, fill=False)
        
        pdf.set_font("Helvetica", size=10, style='')
        
        # Below Logo Customer Details
        pdf.set_xy(x=7, y=61)
        pdf.cell(43, 7, txt=f"Customer Name:", ln=True, align='L', fill=True, border=1)
        pdf.set_xy(x=48, y=61)
        pdf.cell(43, 7, txt=f"{invoice[3]}", ln=True, align='L', fill=True, border=1)
        pdf.set_xy(x=7, y=68)
        pdf.cell(43, 7, txt=f"Customer Phone:", ln=True, align='L', fill=True, border=1)
        pdf.set_xy(x=48, y=68)
        pdf.cell(43, 7, txt=f"{invoice[4]}", ln=True, align='L', fill=True, border=1)
        # pdf.cell(200, 10, txt=f"Customer Phone: {invoice[4]}", ln=True, align='L')
        # pdf.cell(200, 10, txt=f"Total Amount: {invoice[5]:.2f}", ln=True, align='L')
                
        # Align right with Customer Details
        pdf.set_xy(x=120, y=61)
        pdf.set_fill_color(238, 238, 238)
        pdf.cell(30, 7, txt=f"Account Title:", ln=True, align='L', fill=True, border=1)
        pdf.set_xy(x=150, y=61)
        pdf.cell(55, 7, txt=f"Rameez Ahmed", ln=True, align='L', border=1, fill=False)
        pdf.set_xy(x=120, y=68)
        pdf.cell(30, 7, txt=f"Account Number:", ln=True, align='L', fill=True, border=1)
        pdf.set_xy(x=150, y=68)
        pdf.cell(55, 7, txt=f"00207901029503", ln=True, align='L', border=1, fill=False)
        pdf.set_xy(x=120, y=75)
        pdf.cell(30, 7, txt=f"IBAN:", ln=True, align='L', fill=True, border=1)
        pdf.set_xy(x=150, y=75)
        pdf.cell(55, 7, txt=f"PK58HABB0000207901029503", ln=True, align='L', border=1, fill=False)
        
        # pdf.cell(200, 10, txt="", ln=True, align='L')
        
        pdf.ln()
        
        pdf.set_x(x=5)
        
        pdf.multi_cell_row(5, 40, 10, ["Item Name", "Description", "Price", "Quantity", "Total Price"], to_fill=True)

        pdf.set_font("Helvetica", size=11, style='')

        for item in items:
            pdf.set_x(x=5)
            pdf.multi_cell_row(5, 40, 5, [item[2], item[3], f"{item[4]:.2f}", str(item[5]), f"{item[6]:.2f}"], to_fill=False)
        
        pdf.set_font("Helvetica", size=12)
        
        pdf.set_x(x=5)
        pdf.multi_cell_row(5, 40, 10, ["", "", "", "Total Amount", f"{invoice[5]:.2f}"], to_fill=False)
        pdf.set_x(x=5)
        pdf.multi_cell_row(5, 40, 10, ["", "", "", "Paid Amount", f"{invoice[6]:.2f}"], to_fill=False)
        pdf.set_x(x=5)
        pdf.multi_cell_row(5, 40, 10, ["", "", "", "Remaining Amount", f"{invoice[7]:.2f}"], to_fill=False)
        pdf.set_x(x=5)
        pdf.multi_cell_row(5, 40, 10, ["", "", "", "Paid Status", f"{invoice[8]}"], to_fill=False)
        
        pdf.ln()
                
        # Invoice Header
        pdf.set_font("Helvetica", size=15, style='B')
        pdf.cell(190, 10, txt='ADDITIONAL NOTES', align='C')
        pdf.ln()
        pdf.set_fill_color(0, 0, 0)
        pdf.set_x(x=0)
        pdf.cell(210, 0.5, txt='', align='C', fill=True)
        pdf.ln()
        pdf.ln()
        
        # Reset Colors
        pdf.set_fill_color(255, 255, 255)
        
        pdf.set_x(x=2)
        pdf.set_font("Helvetica", size=12, style='B')
        pdf.cell(w=200, h=6, txt="Payment Terms:")
        pdf.ln()
        
        pdf.set_font("Helvetica", size=10, style='')
        pdf.set_x(x=10)
        pdf.multi_cell(w=200, h=4, txt="- A 50% advance will be given before the event, and the remaining payment will be cleared by the next day of the event. Otherwise, raw data will not be provided for selection.")
        pdf.ln()
        
        pdf.set_x(x=2)
        pdf.set_font("Helvetica", size=12, style='B')
        pdf.cell(w=200, h=4, txt="Terms and Conditions:")
        pdf.ln()
        
        pdf.set_font("Helvetica", size=10, style='')
        pdf.set_x(x=10)
        pdf.multi_cell(w=200, h=4, txt='- No payment will be refunded in case of any mishap or unforeseen situation / circumstances occurred.')
        pdf.ln(1)
        pdf.multi_cell(w=200, h=4, txt='- Client can only provide the extended date of the event.')
        pdf.ln(1)
        pdf.multi_cell(w=200, h=4, txt='- Misbehavior of client will not be accepted')
        pdf.ln(1)
        pdf.multi_cell(w=200, h=4, txt="- If photographer provides any suggestion / advice regarding event management and client don't listen or take it seriously so it will be not our responsibility.")
        pdf.ln(1)
        pdf.multi_cell(w=200, h=4, txt='- Client Pictures will be used on our page regarding marketing purposes at Instagram and Facebook.')
        pdf.ln(1)
        pdf.multi_cell(w=200, h=4, txt='- Ask for update on editing after 15 days of the event.')
        pdf.ln(1)
        pdf.multi_cell(w=200, h=4, txt='Kindly read this E-mail and instructions carefully and reply back to this but E-mail for confirmation. If any query so please contact us on:')
        pdf.ln(1)
        pdf.multi_cell(w=200, h=4, txt='+923142179245')        
        
        pdf_name = f"duplicate_invoices/invoice_{invoice_id}.pdf"
        pdf.output(pdf_name)
        
        QMessageBox.information(self, 'PDF Generated', f'PDF file has been generated: {pdf_name}')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = InvoiceGenerator()
    ex.show()
    sys.exit(app.exec_())
