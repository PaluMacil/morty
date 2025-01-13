# Morty (your friendly amortization calculator)

Morty is a user-friendly amortization calculator built with PySide6, providing a flexible way to calculate and visualize loan repayment schedules.  It offers the following features:

* **Customizable Loan Details:** Input the principal amount, annual interest rate, and loan term in years.
* **Extra Payments:**  Add extra payments to any month to see how they impact the total interest paid and loan duration.  You can even quickly apply an extra payment to all months by clicking the "Extra Payment" column header.
* **Flexible Start Date:** Choose a numbered start month or select a calendar month/year start, which affects how the schedule is displayed.
* **Totals Comparison:** View the total interest paid and total amount paid, with and without extra payments, to easily compare scenarios.
* **Interactive Table:** The amortization table dynamically updates as you adjust loan details or extra payments.
* **Reset Functionality:**  Quickly reset all input fields to their default values.

## Screenshots

![full window screenshot](docs/full-window-screenshot.png)

## Usage

1. **Input Loan Details:** Enter the principal, annual interest rate, and loan term.
2. **Select Start Month (Optional):** Use the dropdown to choose a numbered or calendar month start date. This option affects how the month and year are displayed in the table. If a calendar month is chosen, an additional option to align the years either with the loan start or calendar year appears.
3. **Calculate:** Click the "Calculate" button to generate the amortization table.
4. **Add Extra Payments (Optional):** Double-click a cell in the "Extra Payment" column to enter an extra payment amount for that month. Change multiple extra payments to see their combined effect. The table updates dynamically to reflect changes. Click the "Extra Payment" header to apply a single extra payment to all rows.
5. **Reset:** Click "Reset" to clear all inputs and the table, reverting to default values.

## Packaging

To package for Windows, run:

```
pyinstaller --windowed --onefile --name "Morty" --icon=morty/friendly.ico --add-data "morty/friendly.ico;." morty/main.py
```
