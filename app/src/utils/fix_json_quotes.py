import re


def fix_json_quotes(json_str: str) -> str:
    """
    Convierte JSON malformado a JSON válido
    Casos:
    - Comillas simples → dobles
    - Sin comillas en propiedades → con comillas
    """

    # 1. Reemplazar comillas simples por dobles
    json_str = json_str.replace("'", '"')

    # 2. Agregar comillas a propiedades: {palabra: → {"palabra":
    json_str = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)(\s*):', r'\1"\2"\3:', json_str)

    # 3. Agregar comillas a valores sin comillas después de :
    # Patrón: :valor, o :valor} donde valor no empieza con " o [
    json_str = re.sub(r':(\s*)([^"\[\],{}]+?)(\s*)([,}\]])', r':"\2"\4', json_str)

    return json_str

