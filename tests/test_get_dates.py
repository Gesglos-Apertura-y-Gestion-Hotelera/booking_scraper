import os
import sys
import pytest
from unittest.mock import patch
import datetime
from app.src.utils.get_dates import get_dates


class TestGetDates:

    # 1. Solo un decorador patch -> solo un argumento (mock_getenv)
    @patch('app.src.utils.get_dates.os.getenv')
    def test_args_presentes(self, mock_getenv):
        """Simula: docker run selenium-app personalizado [JSON] 2026-04-01 2026-04-05"""

        json_data = '[{"hotel": "Porto Marina Hotel","competidor": "Hotel Bambu Guatape"}]'

        # El índice 0 es el nombre del script, 1 el modo, 2 el json, 3 check_in, 4 check_out
        test_args = ['main.py', 'personalizado', json_data, '2026-04-01', '2026-04-05']

        # Configuramos el mock para que devuelva None (así usa los argumentos)
        mock_getenv.return_value = None

        # 2. Usamos patch.object aquí para no tener que pasarlo como argumento de la función
        with patch.object(sys, 'argv', test_args):
            resultado = get_dates()
            check_in, check_out = resultado

            # Aserciones
            assert check_in.strftime('%Y-%m-%d') == '2026-04-01'
            assert check_out.strftime('%Y-%m-%d') == '2026-04-05'

    @patch('app.src.utils.get_dates.os.getenv')
    @patch('app.src.utils.get_dates.sys')
    def test_env_check_in(self, mock_sys, mock_getenv):
        # Configuramos el mock para que responda según la clave solicitada
        def side_effect_func(key, default=None):
            if key == 'CHECK_IN': return '2024-02-01'
            if key == 'CHECK_OUT': return ''
            return default  # Para SHEET_DATA u otros

        mock_getenv.side_effect = side_effect_func
        mock_sys.argv = ['script.py', 'modo', '{}', 'ignore', '2024-02-05']


        resultado = get_dates()
        check_in, check_out = resultado

        assert check_in.strftime('%Y-%m-%d') == '2024-02-01'
        assert check_out.strftime('%Y-%m-%d') == '2024-02-05'

    @patch('app.src.utils.get_dates.os.getenv')
    @patch('app.src.utils.get_dates.sys')
    def test_ambos_env(self, mock_sys, mock_getenv):
        """Ambos CHECK_IN y CHECK_OUT en env"""
        mock_sys.argv = ['script.py']
        mock_getenv.side_effect = ['2024-02-10', '2024-02-15']

        resultado = get_dates()
        check_in, check_out = resultado
        assert check_in.strftime('%Y-%m-%d') == '2024-02-10'
        assert check_out.strftime('%Y-%m-%d') == '2024-02-15'

    @patch('app.src.utils.get_dates.sys')
    def test_sin_args_error(self, mock_sys):
        """Sin argumentos suficientes"""
        mock_sys.argv = ['script.py']

        with pytest.raises(IndexError):
            get_dates()

    @patch('app.src.utils.get_dates.os.getenv')
    @patch('app.src.utils.get_dates.sys')
    def test_fecha_invalida(self, mock_sys, mock_getenv):
        """Fecha malformada en args[2] del slice o args[3] del sys.argv"""

        # Debes simular la estructura completa: [0]script, [1]modo, [2]json, [3]check_in, [4]check_out
        json_data = '[]'
        mock_sys.argv = ['script.py', 'personalizado', json_data, '2024-13-01', '2024-02-05']

        # Agregamos 3 valores para las 3 llamadas a getenv (logger, in, out)
        mock_getenv.side_effect = [None, None, None]

        # Ahora el error no será de índice, sino de formato de fecha (ValueError)
        with pytest.raises(ValueError):
            get_dates()

