import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.src.utils.get_dates import get_dates


class TestGetDates:

    @patch('app.src.utils.get_dates.os.getenv')
    @patch('app.src.utils.get_dates.sys')
    def test_args_presentes(self, mock_sys, mock_getenv):
        """Simula Docker: main.py personalizado [JSON] 2026-04-01 2026-04-05"""
        mock_sys.argv = ['main.py', 'personalizado', '[]', '2026-04-01', '2026-04-05']
        mock_getenv.return_value = None  # No env → usa args

        resultado = get_dates()
        check_in, check_out = resultado
        assert check_in.strftime('%Y-%m-%d') == '2026-04-01'
        assert check_out.strftime('%Y-%m-%d') == '2026-04-05'

    @patch('app.src.utils.get_dates.os.getenv')
    @patch('app.src.utils.get_dates.sys')
    def test_env_check_in(self, mock_sys, mock_getenv):
        """CHECK_IN desde env, CHECK_OUT desde args"""
        mock_sys.argv = ['main.py', 'personalizado', '[]', 'ignore', '2024-02-05']
        mock_getenv.side_effect = lambda k, d=None: '2024-02-01' if k == 'CHECK_IN' else None

        resultado = get_dates()
        check_in, check_out = resultado
        assert check_in.strftime('%Y-%m-%d') == '2024-02-01'
        assert check_out.strftime('%Y-%m-%d') == '2024-02-05'

    @patch('app.src.utils.get_dates.os.getenv')
    @patch('app.src.utils.get_dates.sys')
    def test_ambos_env(self, mock_sys, mock_getenv):
        """Ambos desde env"""
        mock_sys.argv = ['main.py']
        mock_getenv.side_effect = ['2024-02-10', '2024-02-15']

        resultado = get_dates()
        check_in, check_out = resultado
        assert check_in.strftime('%Y-%m-%d') == '2024-02-10'
        assert check_out.strftime('%Y-%m-%d') == '2024-02-15'

    @patch('app.src.utils.get_dates.os.getenv')
    @patch('app.src.utils.get_dates.sys')
    def test_sin_args_error(self, mock_sys, mock_getenv):
        """Sin argumentos → sys.exit(1)"""
        mock_sys.argv = ['main.py']
        mock_getenv.return_value = None

        with pytest.raises(SystemExit):
            get_dates()

    @patch('app.src.utils.get_dates.os.getenv')
    @patch('app.src.utils.get_dates.sys')
    def test_fecha_invalida(self, mock_sys, mock_getenv):
        """Fecha malformada → ValueError"""
        mock_sys.argv = ['main.py', 'personalizado', '[]', '2024-13-01', '2024-02-05']
        mock_getenv.return_value = None

        with pytest.raises(ValueError):
            get_dates()

    @patch('app.src.utils.get_dates.os.getenv')
    @patch('app.src.utils.get_dates.sys')
    def test_fecha_pasada(self, mock_sys, mock_getenv):
        """check_in en pasado → sys.exit(1)"""
        mock_sys.argv = ['main.py', 'modo', '2026-02-01', '2026-02-05']  # Antes de hoy
        mock_getenv.return_value = None

        with pytest.raises(SystemExit):
            get_dates()

    @patch('app.src.utils.get_dates.os.getenv')
    @patch('app.src.utils.get_dates.sys')
    def test_check_out_check_in(self, mock_sys, mock_getenv):
        """check_out <= check_in → sys.exit(1)"""
        mock_sys.argv = ['main.py', 'modo', '2026-04-01', '2026-04-01']  # Igual día
        mock_getenv.return_value = None

        with pytest.raises(SystemExit):
            get_dates()