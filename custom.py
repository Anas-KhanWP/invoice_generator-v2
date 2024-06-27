from fpdf import FPDF

class CustomPDF(FPDF):
    # def set_fill_color(self, r, g, b):
    #     super().set_fill_color(r, g, b)
        
    def multi_cell_row(self, cells, width, height, data, to_fill=False):
        # print(f"to_fill parameter value: {to_fill}")  # Print the value of to_fill
        filling = to_fill
        # print(f"Initial filling value: {filling}")

        if to_fill:
            self.set_fill_color(238, 238, 238)  # Set the fill color here
            # print(f"In condition: {filling}")

        x = self.get_x()
        y = self.get_y()
        maxheight = 0
        
        for i in range(cells):
            self.multi_cell(width, height, data[i], fill=filling)
            # print(f"After multi_cell, filling: {filling}")
            if self.get_y() - y > maxheight:
                maxheight = self.get_y() - y
            self.set_xy(x + (width * (i + 1)), y)
        
        for i in range(cells + 1):
            self.line(x + width * i, y, x + width * i, y + maxheight)
        
        self.line(x, y, x + width * cells, y)
        self.line(x, y + maxheight, x + width * cells, y + maxheight)
        
        self.set_y(y + maxheight)


    def generate_invoice(self, items):
        self.set_font("Arial", size=12)
        
        for item in items:
            self.multi_cell_row(5, 30, 5, [item[1], item[2], f"{item[3]:.2f}", str(item[4]), f"{item[5]:.2f}"])
            self.ln()

# Example usage:
# items = [
#     (1, 'Item 1', 'Description 1', 10.0, 2, 20.0),
#     (2, 'Item 2', 'Description 2Description 2Description 2Description 2Description 2Description 2', 15.0, 3, 45.0),
#     (3, 'Item 3', 'Description 3', 5.0, 1, 5.0)
# ]

# pdf = CustomPDF()
# pdf.add_page()
# pdf.generate_invoice(items)
# pdf.output("invoice.pdf")
