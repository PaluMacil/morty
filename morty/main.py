import calendar
import sys
from contextlib import contextmanager
from os import path
from typing import Generator

from PySide6.QtCore import Qt, QEvent, QObject, QModelIndex, QAbstractItemModel
from PySide6.QtGui import QDoubleValidator, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QLabel,
    QPushButton,
    QFormLayout,
    QHeaderView,
    QHBoxLayout,
    QGroupBox,
    QGridLayout,
    QComboBox,
    QRadioButton,
    QStyledItemDelegate,
    QLineEdit,
    QInputDialog,
    QTabWidget,
    QStyleOptionViewItem
)


class Plan(QWidget):
    """
    A single amortization plan, encapsulated in a QWidget.
    """

    DEFAULT_PRINCIPAL = "348300"
    DEFAULT_ANNUAL_RATE = "6.75"
    DEFAULT_YEARS = "30"

    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)

        # Input fields
        self.input_form = QFormLayout()
        self.principal_input = QLineEdit(self.DEFAULT_PRINCIPAL)
        self.annual_rate_input = QLineEdit(self.DEFAULT_ANNUAL_RATE)
        self.years_input = QLineEdit(self.DEFAULT_YEARS)
        self.input_form.addRow("Principal ($):", self.principal_input)
        self.input_form.addRow("Annual Interest Rate (%):", self.annual_rate_input)
        self.input_form.addRow("Loan Term (Years):", self.years_input)
        self.layout.addLayout(self.input_form)
        self.start_month_dropdown = QComboBox()
        self.start_month_dropdown.addItems(["1 (numbered)"] + [calendar.month_abbr[m] for m in range(1, 13)])
        self.start_month_dropdown.currentIndexChanged.connect(self.update_year_start_visibility)
        self.input_form.addRow("Start Month:", self.start_month_dropdown)
        self.year_start_group = QGroupBox("Year Start")
        self.year_start_group.setVisible(False)
        self.year_start_layout = QHBoxLayout()
        self.loan_year_button = QRadioButton("Loan Start")
        self.loan_year_button.setChecked(True)
        self.calendar_year_button = QRadioButton("Calendar Year")
        self.year_start_layout.addWidget(self.loan_year_button)
        self.year_start_layout.addWidget(self.calendar_year_button)
        self.year_start_group.setLayout(self.year_start_layout)
        self.input_form.addRow("", self.year_start_group)
        self.loan_year_button.toggled.connect(self.calculate_amortization)
        self.calendar_year_button.toggled.connect(self.calculate_amortization)

        # Button layout (horizontal)
        self.button_layout = QHBoxLayout()
        self.calculate_button = QPushButton("Calculate")
        self.calculate_button.clicked.connect(self.calculate_amortization)
        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_calculator)  # Connect to reset function
        self.button_layout.addWidget(self.calculate_button)
        self.button_layout.addWidget(self.reset_button)
        self.layout.addLayout(self.button_layout)

        # Totals Group Box
        self.totals_group_box = QGroupBox("Totals")
        self.totals_group_box.setVisible(False)
        self.totals_layout = QGridLayout()  # Grid layout for 2x2 arrangement
        self.totals_group_box.setLayout(self.totals_layout)
        # Labels (initialized as empty; will be populated in calculate_amortization)
        self.interest_paid_label = QLabel("")
        self.interest_no_extra_label = QLabel("")
        self.total_paid_label = QLabel("")
        self.total_no_extra_label = QLabel("")
        self.sum_of_selected_label = QLabel("Sum of Selected: $0.00")
        self.sum_of_selected_label.setVisible(False)

        self.totals_layout.addWidget(self.interest_paid_label, 0, 0, alignment=Qt.AlignLeft)  # row 0, column 0
        self.totals_layout.addWidget(self.total_paid_label, 0, 1, alignment=Qt.AlignRight)  # row 0, column 1
        self.totals_layout.addWidget(self.interest_no_extra_label, 1, 0, alignment=Qt.AlignLeft)  # row 1, column 0
        self.totals_layout.addWidget(self.total_no_extra_label, 1, 1, alignment=Qt.AlignRight)  # row 1, column 1
        self.totals_layout.addWidget(self.sum_of_selected_label, 2, 0, 1, 2, alignment=Qt.AlignLeft)

        self.layout.addWidget(self.totals_group_box)
        self.total_interest_no_extra_label = QLabel("")
        self.totals_layout.addWidget(self.total_interest_no_extra_label, 0, 1,
                                     alignment=Qt.AlignRight)

        # Table for amortization schedule
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["Month", "Total Payment", "Principal Payment", "Interest Payment", "Remaining Balance"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # Set the delegate for the "Extra Payment" column
        currency_delegate = CurrencyDelegate(self.table)
        self.table.setItemDelegateForColumn(3, currency_delegate)
        self.table.itemChanged.connect(self.handle_extra_payment_change)
        self.table.itemSelectionChanged.connect(self.update_sum_of_selected)
        self.table.horizontalHeader().sectionClicked.connect(self.handle_header_click)
        self.update_row_number_visibility()
        self.layout.addWidget(self.table)

        self.installEventFilter(self)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """
        Filters events to handle key presses, particularly the Return key.

        Args:
            obj (QObject): The object where the event occurred.
            event (QEvent): The event being filtered.

        Returns:
            bool: True if the event was handled; otherwise, False.
        """
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Return:
            self.calculate_amortization()
            return True  # Mark event as handled
        return super().eventFilter(obj, event)

    @contextmanager
    def pause_item_changed_signal(self) -> Generator:
        """
        Context manager to temporarily disconnect the itemChanged signal.

        Yields:
            None: Allows the encapsulated block of code to execute without the signal.
        """
        self.table.itemChanged.disconnect(self.handle_extra_payment_change)
        try:
            yield
        finally:
            self.table.itemChanged.connect(self.handle_extra_payment_change)

    def reset_calculator(self) -> None:
        """Resets the calculator to initial state."""
        self.principal_input.setText(self.DEFAULT_PRINCIPAL)
        self.annual_rate_input.setText(self.DEFAULT_ANNUAL_RATE)
        self.years_input.setText(self.DEFAULT_YEARS)
        self.table.setRowCount(0)  # Clears the table
        self.start_month_dropdown.setCurrentText("1 (numbered)")
        self.calculate_amortization()

    def update_year_start_visibility(self) -> None:
        """
        Shows or hides the 'year start' group based on the start month selection and recalculates the amortization.
        """
        start_month_text = self.start_month_dropdown.currentText()
        if start_month_text in ["1 (numbered)", "Jan"]:
            self.year_start_group.setVisible(False)
        else:
            self.year_start_group.setVisible(True)
        self.update_row_number_visibility()
        self.calculate_amortization()

    def update_row_number_visibility(self) -> None:
        """Update the visibility of row numbers based on the Start Month setting."""
        start_month_text = self.start_month_dropdown.currentText()
        if start_month_text == "1 (numbered)":
            self.table.verticalHeader().setVisible(False)
        else:
            self.table.verticalHeader().setVisible(True)

    def calculate_amortization(self) -> None:
        """
        Calculates and displays the amortization table, accounting for extra payments.

        Raises:
            ValueError: If input values cannot be converted into the appropriate data types for calculation.
        """
        try:
            principal = float(self.principal_input.text())
            annual_rate = float(self.annual_rate_input.text())
            years = int(self.years_input.text())

            extra_payments = self._get_extra_payments(self.table.rowCount())

            amortization, total_interest = self._calculate_amortization_table(
                principal, annual_rate, years, extra_payments
            )
            self._display_amortization_table(amortization)

            # Calculate and display "no extra payment" values for comparison.
            # The following lines are redundant and should be removed
            # amortization_no_extra, total_interest_no_extra = self._calculate_amortization_table(principal, annual_rate, years)
            # total_paid_no_extra = sum(entry['Total Payment'] for entry in amortization_no_extra)
            # self.interest_no_extra_label.setText(f"Interest Paid (No Extra): ${total_interest_no_extra:,.2f}")
            # self.total_no_extra_label.setText(f"Total Paid (No Extra): ${total_paid_no_extra:,.2f}")

            self.totals_group_box.setVisible(True)
            self.totals_group_box.setVisible(True)
            # The following lines are redundant and should be removed
            # amortization_no_extra, total_interest_no_extra = self._calculate_amortization_table(principal, annual_rate, years)
            # total_paid_no_extra = sum(entry['Total Payment'] for entry in amortization_no_extra)
            # self.interest_no_extra_label.setText(f"Interest Paid (No Extra): ${total_interest_no_extra:,.2f}")
            # self.total_no_extra_label.setText(f"Total Paid (No Extra): ${total_paid_no_extra:,.2f}")

            self.totals_group_box.setVisible(True)
            self.totals_group_box.setVisible(True)

        except ValueError as e:
            print(f"Invalid input: {e}")

    def _calculate_amortization_table(
        self, principal: float, annual_rate: float, years: int, extra_payments: list[float] = None
    ) -> tuple[list[dict[str, float]], float]:
        """
        Calculate the amortization table, which determines monthly payments, interest, and the remaining balance.

        Args:
            principal (float): The loan amount.
            annual_rate (float): The annual interest rate, expressed as a percentage.
            years (int): The loan term, in years.
            extra_payments (List[float]): A list of extra payments for each month.

        Returns:
            Tuple[List[Dict[str, float]], float]: The amortization table and total interest paid.
        """
        monthly_rate = annual_rate / 12 / 100
        total_payments = years * 12

        # Calculate monthly payment (excluding extra payments)
        monthly_payment = principal * (monthly_rate * (1 + monthly_rate) ** total_payments) / (
            (1 + monthly_rate) ** total_payments - 1
        )

        # Initialize variables
        balance = principal
        amortization_table = []
        total_interest = 0.0
        month = 1

        while balance > 0:
            interest = balance * monthly_rate
            principal_payment = monthly_payment - interest
            extra_payment = extra_payments[month - 1] if extra_payments and month <= len(extra_payments) else 0
            total_payment = monthly_payment + extra_payment

            # Check if the total payment exceeds the remaining balance
            if total_payment > balance + interest:
                total_payment = balance + interest
                principal_payment = balance

            balance -= (principal_payment + extra_payment)
            total_interest += interest

            amortization_table.append(
                {
                    "Month": month,
                    "Total Payment": total_payment,
                    "Principal Payment": principal_payment,  # Principal from regular payment
                    "Extra Payment": extra_payment,  # Added extra payment column
                    "Interest Payment": interest,
                    "Remaining Balance": max(balance, 0),
                }
            )

            month += 1
        # remove potential additional rows from UI table
        self.table.setRowCount(len(amortization_table))

        return amortization_table, total_interest

    def handle_header_click(self, logical_index: int) -> None:
        """
        Handle clicks on the table header.
        If the "Extra Payment" column is clicked, prompt the user for a value and apply it to the entire column.
        """
        if logical_index == 3:  # "Extra Payment" column
            value, ok = QInputDialog.getDouble(
                self, "Extra Payment", "Enter extra payment to apply to all rows:", decimals=2
            )
            if ok:
                for row in range(self.table.rowCount()):
                    item = self.table.item(row, 3)
                    if item:
                        item.setData(Qt.EditRole, value)
                    else:
                        new_item = QTableWidgetItem()
                        new_item.setData(Qt.EditRole, value)
                        self.table.setItem(row, 3, new_item)

    def update_sum_of_selected(self) -> None:
        selected_items = self.table.selectedItems()
        total_sum = 0.0

        for item in selected_items:
            try:
                value = float(item.text().replace(",", ""))
                total_sum += value
            except ValueError:
                pass

        if total_sum > 0:
            self.sum_of_selected_label.setText(f"Sum of Selected: ${total_sum:,.2f}")
            self.sum_of_selected_label.setVisible(True)
        else:
            self.sum_of_selected_label.setVisible(False)

    def _get_extra_payments(self, num_rows: int) -> list[float]:
        """Retrieves extra payments from the table's model data."""
        extra_payments = [0.0] * num_rows
        for row in range(num_rows):
            item = self.table.item(row, 3)  # Index of Extra Payment column
            if item:
                try:
                    extra_payments[row] = float(item.text().replace(",", ""))
                except ValueError:
                    pass
        return extra_payments

    def _display_amortization_table(self, amortization: list[dict[str, float]]) -> None:
        """
        Display the amortization table in the UI.

        Args:
            amortization (List[Dict[str, float]]): The amortization table to display.
        """
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["Month", "Total Payment", "Principal Payment", "Extra Payment", "Interest Payment", "Remaining Balance"]
        )
        self.table.setRowCount(len(amortization))
        with self.pause_item_changed_signal():
            for row_num, entry in enumerate(amortization):
                month_num = int(entry['Month'])
                start_month_text = self.start_month_dropdown.currentText()

                if start_month_text != "1 (numbered)":
                    try:
                        start_month_num = list(calendar.month_abbr).index(start_month_text)
                    except ValueError:
                        start_month_num = 1  # Default to Jan if not found

                    month_name = calendar.month_abbr[(month_num + start_month_num - 2) % 12 + 1]
                    if self.loan_year_button.isChecked():
                        year_offset = (month_num - 1) // 12  # Offset based on loan start
                    elif self.calendar_year_button.isChecked():
                        year_offset = (month_num + start_month_num - 2) // 12
                    else:
                        raise NotImplemented("newly added radio button not configured")
                    month_str = f"{month_name} Y{year_offset + 1}"
                else:
                    month_str = str(month_num)

                for col_num, (col_name, value) in enumerate(entry.items()):
                    if col_name == "Month":
                        item = self.table.item(row_num, col_num)
                        if item:
                            item.setText(month_str)  # Update text if item exists to avoid overwriting
                        else:
                            item = QTableWidgetItem(month_str)
                            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                            self.table.setItem(row_num, col_num, item)
                    elif col_name == "Extra Payment":
                        item = QTableWidgetItem()
                        item.setData(Qt.EditRole, value)  # Use setData for correct formatting
                        self.table.setItem(row_num, col_num, item)
                    else:  # Format other numeric data, but not editable
                        item = QTableWidgetItem(f"{value:,.2f}")
                        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                        self.table.setItem(row_num, col_num, item)

    def handle_extra_payment_change(self, cell: QTableWidgetItem) -> None:
        """Handles changes to the 'Extra Payment' column."""
        if cell.column() != 3:  # Early return if not the "Extra Payment" column
            return
        row = cell.row()
        if row < 0:  # Early return if row index is invalid
            return
        try:
            with self.pause_item_changed_signal():
                principal = float(self.principal_input.text())
                annual_rate = float(self.annual_rate_input.text())
                years = int(self.years_input.text())

                extra_payments = self._get_extra_payments(self.table.rowCount())  # Retrieve fresh extra payments.
                amortization, total_interest = self._calculate_amortization_table(principal, annual_rate, years,
                                                                                  extra_payments)
                # Update only the necessary cells in the table
                for row_index, entry in enumerate(amortization):  # Use the correct row index
                    for col_index, (col_name, value) in enumerate(entry.items()):
                        # the Month and Extra Payment, which is user-entered,
                        if col_name in {"Month", "Extra Payment"}:
                            continue
                        item = self.table.item(row_index, col_index)
                        if item:
                            item.setText(f"{value:,.2f}")
                        else:
                            new_item = QTableWidgetItem(f"{value:,.2f}")
                            new_item.setFlags(
                                new_item.flags() & ~Qt.ItemIsEditable)
                            self.table.setItem(row_index, col_index, new_item)
                self.update_totals_display(amortization, total_interest, principal, annual_rate, years)
        except ValueError:
            pass

    def update_totals_display(
            self,
            amortization: list[dict[str, float]],
            total_interest: float,
            principal: float,
            annual_rate: float,
            years: int
    ) -> None:
        total_paid = sum(entry['Total Payment'] for entry in amortization)
        self.interest_paid_label.setText(f"Interest Paid: ${total_interest:,.2f}")
        self.total_paid_label.setText(f"Total Paid: ${total_paid:,.2f}")

        # Calculate and display "no extra payment" values for comparison.
        amortization_no_extra, total_interest_no_extra = self._calculate_amortization_table(principal, annual_rate, years)
        total_paid_no_extra = sum(entry['Total Payment'] for entry in amortization_no_extra)
        self.interest_no_extra_label.setText(f"Interest Paid (No Extra): ${total_interest_no_extra:,.2f}")
        self.total_no_extra_label.setText(f"Total Paid (No Extra): ${total_paid_no_extra:,.2f}")

        self.totals_group_box.setVisible(True)


class CurrencyDelegate(QStyledItemDelegate):
    def __init__(self, parent: QWidget | None=None):
        super().__init__(parent)

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget:
        editor = QLineEdit(parent)
        validator = QDoubleValidator(0.0, float('inf'), 2, editor)
        validator.setNotation(QDoubleValidator.StandardNotation)
        editor.setValidator(validator)
        return editor

    def setEditorData(self, editor: QLineEdit, index: QModelIndex) -> None:
        value = index.model().data(index, Qt.DisplayRole)
        editor.setText(str(value))

    def setModelData(self, editor: QLineEdit, model: QAbstractItemModel, index: QModelIndex) -> None:
        value = editor.text()
        model.setData(index, value, Qt.EditRole)


class AmortizationCalculator(QMainWindow):
    """
    A PySide6-based amortization calculator with a UI for flexible calculations.
    Users can input loan details, edit extra payments, and view the amortization table.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Morty (your friendly amortization calculator)")
        self.setGeometry(100, 100, 800, 1100)
        bundle_dir = path.abspath(path.dirname(__file__))
        icon_path = path.join(bundle_dir, "friendly.ico")  # path when bundled by PyInstaller
        self.setWindowIcon(QIcon(icon_path))

        # Main widget and layout
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.layout = QVBoxLayout(self.main_widget)

        # Tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.layout.addWidget(self.tab_widget)

        # Add a button to create new tabs
        self.add_tab_button = QPushButton("Add Plan")
        self.add_tab_button.clicked.connect(self.add_tab)
        self.layout.addWidget(self.add_tab_button)

        # Add the first tab
        self.add_tab()

    def add_tab(self) -> None:
        """Adds a new tab with a Plan widget."""
        new_plan = Plan()
        tab_index = self.tab_widget.addTab(new_plan, f"Plan {self.tab_widget.count() + 1}")
        self.tab_widget.setCurrentIndex(tab_index)

    def close_tab(self, index: int) -> None:
        """Closes the tab at the specified index."""
        self.tab_widget.removeTab(index)
        # Rename remaining tabs
        for i in range(self.tab_widget.count()):
            self.tab_widget.setTabText(i, f"Plan {i + 1}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AmortizationCalculator()
    window.show()
    sys.exit(app.exec())
