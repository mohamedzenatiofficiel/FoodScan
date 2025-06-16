import importlib.util
import sys
import types
from unittest.mock import patch, MagicMock

# Stub external dependencies so streamlit.py can be imported without installing them
requests_stub = types.ModuleType('requests')
requests_stub.get = lambda *a, **k: None
sys.modules['requests'] = requests_stub

pyzbar_module = types.ModuleType('pyzbar')
pyzbar_pybar = types.ModuleType('pyzbar.pyzbar')
pyzbar_pybar.decode = lambda img: []
pyzbar_module.pyzbar = pyzbar_pybar
sys.modules['pyzbar'] = pyzbar_module
sys.modules['pyzbar.pyzbar'] = pyzbar_pybar

pil_stub = types.ModuleType('PIL')
pil_image_stub = types.ModuleType('PIL.Image')
pil_image_stub.open = lambda f: None
pil_stub.Image = pil_image_stub
sys.modules['PIL'] = pil_stub
sys.modules['PIL.Image'] = pil_image_stub

st_lib = types.ModuleType('streamlit')
for attr in ['title', 'file_uploader', 'image', 'button', 'success', 'error', 'table']:
    setattr(st_lib, attr, lambda *args, **kwargs: None)

def cache_decorator(func=None, **kwargs):
    """Simple caching decorator used for tests."""
    from functools import lru_cache
    if func is None:
        def wrapper(f):
            return cache_decorator(f, **kwargs)
        return wrapper
    return lru_cache(maxsize=None)(func)

st_lib.cache_data = cache_decorator
st_lib.experimental_memo = cache_decorator
sys.modules['streamlit'] = st_lib

# Import application module under a different name to avoid conflict with the stubbed library
spec = importlib.util.spec_from_file_location('app_module', 'streamlit.py')
app_module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = app_module
spec.loader.exec_module(app_module)

read_barcode_from_image = app_module.read_barcode_from_image
get_product_info = app_module.get_product_info

# Test read_barcode_from_image with valid barcode
@patch('app_module.decode')
def test_read_barcode_valid(mock_decode):
    mock_obj = MagicMock()
    mock_obj.data = b'1234567890123'
    mock_decode.return_value = [mock_obj]
    result = read_barcode_from_image(MagicMock())
    assert result == '1234567890123'

# Test read_barcode_from_image with no barcode
@patch('app_module.decode')
def test_read_barcode_invalid(mock_decode):
    mock_decode.return_value = []
    result = read_barcode_from_image(MagicMock())
    assert result is None

# Test get_product_info with successful API response
@patch('app_module.requests.get')
def test_get_product_info_success(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'status': 1,
        'product': {
            'product_name': 'Test Product',
            'ingredients_text': 'Water, Sugar',
            'nutriscore_grade': 'a'
        }
    }
    mock_get.return_value = mock_response

    get_product_info.cache_clear()

    name, ingredients, score = get_product_info('123456')

    assert name == 'Test Product'
    assert ingredients == 'Water, Sugar'
    assert score == 'a'

# Test get_product_info when product not found
@patch('app_module.requests.get')
def test_get_product_info_not_found(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'status': 0
    }
    mock_get.return_value = mock_response

    get_product_info.cache_clear()

    name, ingredients, score = get_product_info('0000')

    assert name == 'Produit non trouv\u00e9.'
    assert ingredients is None
    assert score is None

# Test get_product_info when API returns error status
@patch('app_module.requests.get')
def test_get_product_info_api_error(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_get.return_value = mock_response

    get_product_info.cache_clear()

    name, ingredients, score = get_product_info('123456')

    assert name == 'Erreur lors de la r\u00e9cup\u00e9ration des donn\u00e9es.'
    assert ingredients is None
    assert score is None

# Ensure repeated calls use cached result
@patch('app_module.requests.get')
def test_get_product_info_cache(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'status': 1,
        'product': {
            'product_name': 'Cached Product',
            'ingredients_text': 'Water',
            'nutriscore_grade': 'b'
        }
    }
    mock_get.return_value = mock_response

    get_product_info.cache_clear()

    # First call should hit the network
    result1 = get_product_info('9999')
    assert result1[0] == 'Cached Product'

    # Clear mock to detect additional network calls
    mock_get.reset_mock()
    result2 = get_product_info('9999')
    assert result2 == result1
    mock_get.assert_not_called()
