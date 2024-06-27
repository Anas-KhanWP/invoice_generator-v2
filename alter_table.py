import sqlite3

def alter_invoices_table():
    conn = sqlite3.connect('invoices.db')
    c = conn.cursor()

    # Add new columns
    c.execute("ALTER TABLE invoices ADD COLUMN paid_amount REAL DEFAULT 0")
    c.execute("ALTER TABLE invoices ADD COLUMN remaining_amount REAL DEFAULT 0")
    c.execute("ALTER TABLE invoices ADD COLUMN paid_status TEXT DEFAULT 'Unpaid'")

    conn.commit()
    conn.close()

alter_invoices_table()
