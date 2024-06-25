import sys
import sqlite3
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QFormLayout, QLabel, QLineEdit, 
                             QPushButton, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView, QDateEdit)
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
              total_amount REAL)''')

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
        
        self.formLayout.addRow('Date:', self.dateInput)
        self.formLayout.addRow('Venue:', self.venueInput)
        self.formLayout.addRow('Customer Name:', self.customerInput)
        self.formLayout.addRow('Customer Phone:', self.phoneInput)
        
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

        if date and venue and customer_name and customer_phone and self.itemsTable.rowCount() > 0:
            conn = sqlite3.connect('invoices.db')
            c = conn.cursor()
            c.execute("INSERT INTO invoices (date, venue, customer_name, customer_phone, total_amount) VALUES (?, ?, ?, ?, ?)",
                    (date, venue, customer_name, customer_phone, self.calculate_total_amount()))
            invoice_id = c.lastrowid

            for row in range(self.itemsTable.rowCount()):
                name = self.itemsTable.item(row, 0).text()
                description = self.itemsTable.item(row, 1).text()
                price = float(self.itemsTable.item(row, 2).text())
                quantity = int(self.itemsTable.item(row, 3).text())
                total_price = float(self.itemsTable.item(row, 4).text())
                c.execute("INSERT INTO invoice_items (invoice_id, name, description, price, quantity, total_price) VALUES (?, ?, ?, ?, ?, ?)",
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

            pdf.set_font("Helvetica", size=12)

            pdf.cell(200, 10, txt=f"Invoice ID: {invoice[0]}", ln=True, align='L')
            pdf.cell(200, 10, txt=f"Date: {invoice[1]}", ln=True, align='L')
            pdf.cell(200, 10, txt=f"Venue: {invoice[2]}", ln=True, align='L')
            pdf.cell(200, 10, txt=f"Customer Name: {invoice[3]}", ln=True, align='L')
            pdf.cell(200, 10, txt=f"Customer Phone: {invoice[4]}", ln=True, align='L')
            pdf.cell(200, 10, txt=f"Total Amount: {invoice[5]:.2f}", ln=True, align='L')

            pdf.cell(200, 10, txt="", ln=True, align='L')

            pdf.multi_cell_row(5, 40, 10, ["Item Name", "Description", "Price", "Quantity", "Total Price"])

            pdf.set_font("Helvetica", size=10)

            for item in items:
                pdf.multi_cell_row(5, 40, 5, [item[2], item[3], f"{item[4]:.2f}", str(item[5]), f"{item[6]:.2f}"])

            pdf_name = f"invoice_{invoice_id}.pdf"
            pdf.output(pdf_name)

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
        self.itemsTable.setRowCount(0)
        self.totalAmountLabel.setText('Total Amount: 0.0')
    
    def view_invoices(self):
        self.invoiceWindow = InvoiceViewer()
        self.invoiceWindow.show()

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
        
        self.tableWidget.setRowCount(len(invoices))
        self.tableWidget.setColumnCount(6)
        self.tableWidget.setHorizontalHeaderLabels(['Invoice ID', 'Date', 'Venue', 'Customer Name', 'Customer Phone', 'Total Amount'])
        
        for row_num, row_data in enumerate(invoices):
            for col_num, data in enumerate(row_data):
                self.tableWidget.setItem(row_num, col_num, QTableWidgetItem(str(data)))
        
        conn.close()
        
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
        
        pdf.set_font("Helvetica", size=12)
        
        pdf.cell(200, 10, txt=f"Invoice ID: {invoice[0]}", ln=True, align='L')
        pdf.cell(200, 10, txt=f"Date: {invoice[1]}", ln=True, align='L')
        pdf.cell(200, 10, txt=f"Venue: {invoice[2]}", ln=True, align='L')
        pdf.cell(200, 10, txt=f"Customer Name: {invoice[3]}", ln=True, align='L')
        pdf.cell(200, 10, txt=f"Customer Phone: {invoice[4]}", ln=True, align='L')
        pdf.cell(200, 10, txt=f"Total Amount: {invoice[5]:.2f}", ln=True, align='L')
        
        pdf.cell(200, 10, txt="", ln=True, align='L')
        
        # pdf.cell(40, 10, txt="Item Name", border=1)
        # pdf.cell(60, 10, txt="Description", border=1)
        # pdf.cell(30, 10, txt="Price", border=1)
        # pdf.cell(30, 10, txt="Quantity", border=1)
        # pdf.cell(30, 10, txt="Total Price", border=1)
        pdf.ln()
        
        pdf.multi_cell_row(5, 40, 10, ["Item Name", "Description", "Price", "Quantity", "Total Price"])
        
        pdf.set_font("Helvetica", size=10)
        
        for item in items:
            pdf.multi_cell_row(5, 40, 5, [item[2], item[3], f"{item[4]:.2f}", str(item[5]), f"{item[6]:.2f}"])
        
        pdf_name = f"invoice_{invoice_id}.pdf"
        pdf.output(pdf_name)
        
        QMessageBox.information(self, 'PDF Generated', f'PDF file has been generated: {pdf_name}')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = InvoiceGenerator()
    ex.show()
    sys.exit(app.exec_())
