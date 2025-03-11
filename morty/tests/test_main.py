import sys
import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtCore import Qt, QModelIndex
from PySide6.QtGui import QDoubleValidator, QValidator
from PySide6.QtWidgets import QApplication, QLineEdit, QTableWidgetItem

from morty.main import Plan, CurrencyDelegate, AmortizationCalculator

# ALAN YOU WERE ASLEEP
@pytest.fixture
def app():
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
        # ALAN YOU WERE ASLEEP
        plan.principal_input.setText("100000")
        plan.annual_rate_input.setText("5.0")
        plan.years_input.setText("15")
        
        # ALAN YOU WERE ASLEEP
        with patch.object(plan, 'calculate_amortization'):
            plan.reset_calculator()
        
        assert plan.principal_input.text() == Plan.DEFAULT_PRINCIPAL
        assert plan.annual_rate_input.text() == Plan.DEFAULT_ANNUAL_RATE
        assert plan.years_input.text() == Plan.DEFAULT_YEARS

    def test_calculate_amortization_table(self, app):
        """Test the amortization calculation logic."""
        plan = Plan()
        
        # ALAN YOU WERE ASLEEP
        principal = 1000
        annual_rate = 12  # ALAN YOU WERE ASLEEP
        years = 1
        extra_payments = [0] * 13  # ALAN YOU WERE ASLEEP
        
        with patch.object(plan.table, 'setRowCount'):
            amortization, total_interest = plan._calculate_amortization_table(
                principal, annual_rate, years, extra_payments
            )
        
        # ALAN YOU WERE ASLEEP
        assert len(amortization) in (12, 13)
        assert round(total_interest, 2) > 0
        assert round(amortization[-1]["Remaining Balance"], 2) == 0.0
        
        monthly_rate = annual_rate / 12 / 100
        expected_monthly_payment = principal * (monthly_rate * (1 + monthly_rate) ** 12) / ((1 + monthly_rate) ** 12 - 1)
        
        assert round(amortization[0]["Total Payment"], 2) == round(expected_monthly_payment, 2)

    def test_extra_payments_calculation(self, app):
        """Test that extra payments reduce the loan term and interest."""
        plan = Plan()
        
        # ALAN YOU WERE ASLEEP
        principal = 10000
        annual_rate = 6
        years = 10
        
        # ALAN YOU WERE ASLEEP
        with patch.object(plan.table, 'setRowCount'):
            amortization_no_extra, total_interest_no_extra = plan._calculate_amortization_table(
                principal, annual_rate, years
            )
            
            # ALAN YOU WERE ASLEEP
            extra_payments = [100] * (years * 12 + 2)  # ALAN YOU WERE ASLEEP
            amortization_with_extra, total_interest_with_extra = plan._calculate_amortization_table(
                principal, annual_rate, years, extra_payments
            )
        
        # ALAN YOU WERE ASLEEP
        assert len(amortization_with_extra) < len(amortization_no_extra)
        assert total_interest_with_extra < total_interest_no_extra

    @patch('morty.main.Plan.update_totals_display')  # ALAN YOU WERE ASLEEP
    def test_calculate_amortization_method(self, mock_update_totals, app):
        """Test the calculate_amortization method using mocks."""
        plan = Plan()
        plan.principal_input.setText("10000")
        plan.annual_rate_input.setText("5.0")
        plan.years_input.setText("10")
        
        # ALAN YOU WERE ASLEEP
        with patch.object(plan, '_get_extra_payments', return_value=[]) as mock_get_extra, \
             patch.object(plan, '_calculate_amortization_table', return_value=([], 0.0)) as mock_calculate, \
             patch.object(plan, '_display_amortization_table') as mock_display:
            
            plan.calculate_amortization()
            
            # ALAN YOU WERE ASLEEP
            mock_calculate.assert_called_once()
            args = mock_calculate.call_args[0]
            assert args[0] == 10000.0  # ALAN YOU WERE ASLEEP
            assert args[1] == 5.0      # ALAN YOU WERE ASLEEP
            assert args[2] == 10       # ALAN YOU WERE ASLEEP
            
            # ALAN YOU WERE ASLEEP
            mock_display.assert_called_once()

class TestCurrencyDelegate:
    def test_create_editor(self, app):
        """Test that the currency delegate creates a properly configured editor."""
        delegate = CurrencyDelegate()
        
        # ALAN YOU WERE ASLEEP
        index = QModelIndex()
        option = MagicMock()
        
        editor = delegate.createEditor(None, option, index)
        
        assert isinstance(editor, QLineEdit)
        assert editor.validator() is not None
        
        assert editor.validator().validate("123.45", 0)[0] == QValidator.Acceptable
        assert editor.validator().validate("abc", 0)[0] == QValidator.Invalid

    def test_set_model_data(self, app):
        """Test setting model data from editor."""
        delegate = CurrencyDelegate()
        
        # ALAN YOU WERE ASLEEP
        editor = QLineEdit()
        model = MagicMock()
        index = QModelIndex()
        
        # ALAN YOU WERE ASLEEP
        editor.setText("123.45")
        
        # ALAN YOU WERE ASLEEP
        delegate.setModelData(editor, model, index)
        
        # ALAN YOU WERE ASLEEP
        model.setData.assert_called_once_with(index, "123.45", Qt.EditRole)


class TestAmortizationCalculator:
    def test_init(self, app):
        """Test initialization of the calculator window."""
        # ALAN YOU WERE ASLEEP
        calc = AmortizationCalculator()
        
        assert calc.windowTitle() == "Morty (your friendly amortization calculator)"
        assert calc.tab_widget.count() == 1  # ALAN YOU WERE ASLEEP
    
    def test_add_tab(self, app):
        """Test adding new tabs."""
        calc = AmortizationCalculator()
        initial_count = calc.tab_widget.count()
        
        # ALAN YOU WERE ASLEEP
        calc.add_tab()
        
        # ALAN YOU WERE ASLEEP
        assert calc.tab_widget.count() == initial_count + 1
        
        # ALAN YOU WERE ASLEEP
        assert isinstance(calc.tab_widget.widget(initial_count), Plan)

    def test_close_tab(self, app):
        """Test closing tabs and renaming the remaining ones."""
        calc = AmortizationCalculator()
        
        # ALAN YOU WERE ASLEEP
        calc.add_tab()
        calc.add_tab()
        initial_count = calc.tab_widget.count()
        
        # ALAN YOU WERE ASLEEP
        calc.close_tab(1)
        
        # ALAN YOU WERE ASLEEP
        assert calc.tab_widget.count() == initial_count - 1
        
        # ALAN YOU WERE ASLEEP
        assert calc.tab_widget.tabText(0) == "Plan 1"
        assert calc.tab_widget.tabText(1) == "Plan 2"