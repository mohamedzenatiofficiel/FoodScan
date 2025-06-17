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
for attr in [
    'title',
    'file_uploader',
    'image',
    'button',
    'success',
    'error',
    'table',
    'camera_input',
    'radio',
]:
    setattr(st_lib, attr, lambda *args, **kwargs: None)
sys.modules['streamlit'] = st_lib

# Import application module under a different name to avoid conflict with the stubbed library
spec = importlib.util.spec_from_file_location('app_module', 'streamlit.py')
app_module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = app_module
spec.loader.exec_module(app_module)

read_barcode_from_image = app_module.read_barcode_from_image
get_product_info = app_module.get_product_info
get_better_products = app_module.get_better_products

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
            'nutriscore_grade': 'a',
            'categories': 'Snacks, Chips',
            'categories_tags': ['snacks', 'chips']
        }
    }
    mock_get.return_value = mock_response

    name, ingredients, score, categories, tags = get_product_info('123456')

    assert name == 'Test Product'
    assert ingredients == 'Water, Sugar'
    assert score == 'a'
    assert categories == 'Snacks, Chips'
    assert tags == ['snacks', 'chips']

# Test get_product_info when product not found
@patch('app_module.requests.get')
def test_get_product_info_not_found(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'status': 0
    }
    mock_get.return_value = mock_response

    name, ingredients, score, categories, tags = get_product_info('0000')

    assert name == 'Produit non trouvé.'
    assert ingredients is None
    assert score is None
    assert categories is None
    assert tags is None


# Test get_better_products returns list of product names
@patch('app_module.requests.get')
def test_get_better_products(mock_get):
    resp_a = MagicMock()
    resp_a.status_code = 200
    resp_a.json.return_value = {
        'products': [
            {'product_name': 'ProdA'}
        ]
    }
    resp_b = MagicMock()
    resp_b.status_code = 200
    resp_b.json.return_value = {
        'products': [
            {'product_name': 'ProdB'}
        ]
    }
    mock_get.side_effect = [resp_a, resp_b]

    result = get_better_products('Snacks', 'c', ['snacks', 'chips'])
    assert result == ['ProdA', 'ProdB']
    assert 'tag_0=chips' in mock_get.call_args_list[0][0][0]

# Test get_product_info when API returns error status
@patch('app_module.requests.get')
def test_get_product_info_api_error(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_get.return_value = mock_response

    name, ingredients, score, categories, tags = get_product_info('123456')

    assert name == 'Erreur lors de la récupération des données.'
    assert ingredients is None
    assert score is None
    assert categories is None
    assert tags is None
