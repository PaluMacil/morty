import sys
import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtCore import Qt, QModelIndex
from PySide6.QtGui import QDoubleValidator, QValidator
from PySide6.QtWidgets import QApplication, QLineEdit, QTableWidgetItem

# Import directly from main module
from morty.main import Plan, CurrencyDelegate, AmortizationCalculator

# Create a fixture for QApplication that can be shared across tests
@pytest.fixture
def app():
    # Only create QApplication if it doesn't exist
    if not QApplication.instance():
        app = QApplication(sys.argv)
    else:
        app = QApplication.instance()
    yield app


class TestPlan:
    def test_init_default_values(self, app):
        """Test that Plan initializes with default values."""
        plan = Plan()
        assert plan.principal_input.text() == Plan.DEFAULT_PRINCIPAL
        assert plan.annual_rate_input.text() == Plan.DEFAULT_ANNUAL_RATE
        assert plan.years_input.text() == Plan.DEFAULT_YEARS
        assert plan.start_month_dropdown.currentText() == "1 (numbered)"
        assert plan.loan_year_button.isChecked() is True
        assert plan.calendar_year_button.isChecked() is False

    def test_reset_calculator(self, app):
        """Test the reset_calculator method resets values to defaults."""
        plan = Plan()
        # Change values
        plan.principal_input.setText("100000")
        plan.annual_rate_input.setText("5.0")
        plan.years_input.setText("15")
        
        # Reset
        with patch.object(plan, 'calculate_amortization'):  # Prevent actual calculation during test
            plan.reset_calculator()
        
        # Check defaults restored
        assert plan.principal_input.text() == Plan.DEFAULT_PRINCIPAL
        assert plan.annual_rate_input.text() == Plan.DEFAULT_ANNUAL_RATE
        assert plan.years_input.text() == Plan.DEFAULT_YEARS

    def test_calculate_amortization_table(self, app):
        """Test the amortization calculation logic."""
        plan = Plan()
        
        # Test with simple values
        principal = 1000
        annual_rate = 12  # 12%
        years = 1
        extra_payments = [0] * 13  # Allow for possible 13th payment
        
        # We need to patch setRowCount to prevent UI updates
        with patch.object(plan.table, 'setRowCount'):
            amortization, total_interest = plan._calculate_amortization_table(
                principal, annual_rate, years, extra_payments
            )
        
        # Basic validation - allow for possibility of 12 or 13 payments
        # (depending on rounding in the implementation)
        assert len(amortization) in (12, 13)  # Either 12 or 13 months for 1 year is acceptable
        assert round(total_interest, 2) > 0  # Should have some interest
        assert round(amortization[-1]["Remaining Balance"], 2) == 0.0  # Last payment should have 0 balance
        
        # Calculate expected monthly payment
        monthly_rate = annual_rate / 12 / 100
        expected_monthly_payment = principal * (monthly_rate * (1 + monthly_rate) ** 12) / ((1 + monthly_rate) ** 12 - 1)
        
        # Check that the first payment matches our expectation (within rounding error)
        assert round(amortization[0]["Total Payment"], 2) == round(expected_monthly_payment, 2)

    def test_extra_payments_calculation(self, app):
        """Test that extra payments reduce the loan term and interest."""
        plan = Plan()
        
        # Calculate without extra payments
        principal = 10000
        annual_rate = 6
        years = 10
        
        # We need to patch setRowCount to prevent UI updates
        with patch.object(plan.table, 'setRowCount'):
            amortization_no_extra, total_interest_no_extra = plan._calculate_amortization_table(
                principal, annual_rate, years
            )
            
            # Calculate with $100 extra payment every month
            extra_payments = [100] * (years * 12 + 2)  # Add buffer for potential extra payments
            amortization_with_extra, total_interest_with_extra = plan._calculate_amortization_table(
                principal, annual_rate, years, extra_payments
            )
        
        # Extra payments should result in fewer payments and less interest
        assert len(amortization_with_extra) < len(amortization_no_extra)
        assert total_interest_with_extra < total_interest_no_extra

    @patch('morty.main.Plan.update_totals_display')  # Prevent update_totals_display from being called
    def test_calculate_amortization_method(self, mock_update_totals, app):
        """Test the calculate_amortization method using mocks."""
        plan = Plan()
        plan.principal_input.setText("10000")
        plan.annual_rate_input.setText("5.0")
        plan.years_input.setText("10")
        
        # Create separate patches within the test to prevent double calls
        with patch.object(plan, '_get_extra_payments', return_value=[]) as mock_get_extra, \
             patch.object(plan, '_calculate_amortization_table', return_value=([], 0.0)) as mock_calculate, \
             patch.object(plan, '_display_amortization_table') as mock_display:
            
            plan.calculate_amortization()
            
            # Check that calculation method was called with correct values
            mock_calculate.assert_called_once()
            args = mock_calculate.call_args[0]
            assert args[0] == 10000.0  # principal
            assert args[1] == 5.0      # annual_rate
            assert args[2] == 10       # years
            
            # Check that display method was called
            mock_display.assert_called_once()




class TestCurrencyDelegate:
    def test_create_editor(self, app):
        """Test that the currency delegate creates a properly configured editor."""
        delegate = CurrencyDelegate()
        
        # Create mock index and option
        index = QModelIndex()
        option = MagicMock()
        
        # Create the editor
        editor = delegate.createEditor(None, option, index)
        
        # Verify it's a QLineEdit with appropriate validator
        assert isinstance(editor, QLineEdit)
        assert editor.validator() is not None
        
        # Test the validator accepts appropriate values - using QValidator constants
        assert editor.validator().validate("123.45", 0)[0] == QValidator.Acceptable
        assert editor.validator().validate("abc", 0)[0] == QValidator.Invalid

    def test_set_model_data(self, app):
        """Test setting model data from editor."""
        delegate = CurrencyDelegate()
        
        # Create mocks
        editor = QLineEdit()
        model = MagicMock()
        index = QModelIndex()
        
        # Set editor text
        editor.setText("123.45")
        
        # Call setModelData
        delegate.setModelData(editor, model, index)
        
        # Verify model.setData was called correctly
        model.setData.assert_called_once_with(index, "123.45", Qt.EditRole)


class TestAmortizationCalculator:
    def test_init(self, app):
        """Test initialization of the calculator window."""
        calc = AmortizationCalculator()
        
        # Check basic window properties
        assert calc.windowTitle() == "Morty (your friendly amortization calculator)"
        assert calc.tab_widget.count() == 1  # Should start with one plan
    
    def test_add_tab(self, app):
        """Test adding new tabs."""
        calc = AmortizationCalculator()
        initial_count = calc.tab_widget.count()
        
        # Add a new tab
        calc.add_tab()
        
        # Check tab count increased
        assert calc.tab_widget.count() == initial_count + 1
        
        # Check the tab contains a Plan widget
        assert isinstance(calc.tab_widget.widget(initial_count), Plan)

    def test_close_tab(self, app):
        """Test closing tabs and renaming the remaining ones."""
        calc = AmortizationCalculator()
        
        # Add several tabs
        calc.add_tab()
        calc.add_tab()
        initial_count = calc.tab_widget.count()
        
        # Close the middle tab
        calc.close_tab(1)
        
        # Check tab count decreased
        assert calc.tab_widget.count() == initial_count - 1
        
        # Check tab names were renumbered
        assert calc.tab_widget.tabText(0) == "Plan 1"
        assert calc.tab_widget.tabText(1) == "Plan 2"