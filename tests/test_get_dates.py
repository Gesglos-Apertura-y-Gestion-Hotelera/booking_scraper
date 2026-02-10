import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from ..app.src.utils.get_dates import get_dates

class TestGetDates:

    @patch('app.src.utils.get_dates.os.getenv')
    @patch('app.src.utils.get_dates.sys.argv', ['main.py', 'personalizado', '[]', "2026-04-15", "2026-04-20"])
    @patch('app.src.utils.get_dates.date')
    def test_args_presentes(self, mock_date, mock_getenv):
        """Args válidos → fechas correctas"""
        mock_getenv.return_value = ''
        mock_date.today.return_value = datetime(2026, 2, 1).date()

        resultado = get_dates()
        check_in, check_out = resultado
        assert check_in.strftime('%Y-%m-%d') == '2026-04-15'
        assert check_out.strftime('%Y-%m-%d') == '2026-04-20'

    @patch('app.src.utils.get_dates.os.getenv')
    @patch('app.src.utils.get_dates.sys.argv', ['main.py', 'personalizado', '[]', 'junk', '2026-04-20'])
    @patch('app.src.utils.get_dates.date')
    def test_env_check_in(self, mock_date, mock_getenv):
        """CHECK_IN env, CHECK_OUT args"""

        # Usa una función que devuelva valores según la key
        def getenv_side_effect(key, default=None):
            if key == 'CHECK_IN':
                return '2026-04-10'
            elif key == 'CHECK_OUT':
                return ''
            return default

        mock_getenv.side_effect = getenv_side_effect
        mock_date.today.return_value = datetime(2026, 2, 1).date()

        resultado = get_dates()
        check_in, check_out = resultado
        assert check_in.strftime('%Y-%m-%d') == '2026-04-10'
        assert check_out.strftime('%Y-%m-%d') == '2026-04-20'

    @patch('app.src.utils.get_dates.os.getenv')
    @patch('app.src.utils.get_dates.sys.argv', ['main.py'])
    @patch('app.src.utils.get_dates.date')
    def test_ambos_env(self, mock_date, mock_getenv):
        """Ambos desde env"""
        mock_getenv.side_effect = ['2026-04-10', '2026-04-15']
        mock_date.today.return_value = datetime(2026, 2, 1).date()

        resultado = get_dates()
        check_in, check_out = resultado
        assert check_in.strftime('%Y-%m-%d') == '2026-04-10'
        assert check_out.strftime('%Y-%m-%d') == '2026-04-15'

    @patch('app.src.utils.get_dates.os.getenv')
    @patch('app.src.utils.get_dates.sys.argv', ['main.py'])
    def test_sin_args_error(self, mock_getenv):
        """Sin argumentos → sys.exit(1)"""
        mock_getenv.return_value = ''

        with pytest.raises(SystemExit):
            get_dates()

    @patch('app.src.utils.get_dates.os.getenv')
    @patch('app.src.utils.get_dates.sys.argv', ['main.py', 'personalizado', '[]', 'invalid', '2026-04-05'])
    def test_fecha_invalida(self, mock_getenv):
        """Fecha malformada → sys.exit(1)"""
        mock_getenv.return_value = ''

        with pytest.raises(SystemExit):
            get_dates()

    @patch('app.src.utils.get_dates.os.getenv')
    @patch('app.src.utils.get_dates.sys.argv', ['main.py', 'personalizado', '[]', '2026-02-01', '2026-04-05'])
    @patch('app.src.utils.get_dates.date')
    def test_fecha_pasada(self, mock_date, mock_getenv):
        """check_in en pasado → sys.exit(1)"""
        mock_getenv.return_value = ''
        mock_date.today.return_value = datetime(2026, 3, 1).date()

        with pytest.raises(SystemExit):
            get_dates()

    @patch('app.src.utils.get_dates.os.getenv')
    @patch('app.src.utils.get_dates.sys.argv', ['main.py', 'personalizado', '[]', '2026-04-01', '2026-04-01'])
    @patch('app.src.utils.get_dates.date')
    def test_check_out_check_in(self, mock_date, mock_getenv):
        """check_out <= check_in → sys.exit(1)"""
        mock_getenv.return_value = ''
        mock_date.today.return_value = datetime(2026, 2, 1).date()

        with pytest.raises(SystemExit):
            get_dates()