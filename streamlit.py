import streamlit as st
from pyzbar.pyzbar import decode
from PIL import Image
import requests

def read_barcode_from_image(image):
    """
    Lit le code-barres à partir d'une image PIL et retourne les données décodées.
    """
    decoded_objects = decode(image)

    for obj in decoded_objects:
        barcode_data = obj.data.decode("utf-8")
        return barcode_data

    return None

def get_product_info(barcode):
    """
    Retrieve product information from OpenFoodFacts using the barcode.

    Returns:
        name (str or None): Product name or None if the barcode is invalid or an API error occurs.
        ingredients (str or None): Product ingredients or None if the barcode is invalid or an API error occurs.
        nutriscore (str or None): Nutri-Score grade or None if the barcode is invalid or an API error occurs.
    """
    url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()

        if data['status'] == 0:
            return "Produit non trouvé.", None, None

        product = data['product']
        name = product.get('product_name', 'Nom non disponible')
        ingredients = product.get('ingredients_text', 'Ingrédients non disponibles')
        nutriscore = product.get('nutriscore_grade', 'Nutri-Score non disponible')

        return name, ingredients, nutriscore
    else:
        return "Erreur lors de la récupération des données.", None, None

# Configuration de l'interface Streamlit
st.title("Scanner de code-barres et récupération d'informations sur le produit")

uploaded_file = st.file_uploader("Chargez une image contenant un code-barres", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption='Image chargée', use_column_width=True)

    if st.button('Scanner le code-barres'):
        barcode_data = read_barcode_from_image(image)

        if barcode_data:
            st.success(f"Code-barres détecté: {barcode_data}")
            name, ingredients, nutriscore = get_product_info(barcode_data)

            if name:
                # Création du tableau
                product_info = {
                    "Nom du produit": [name],
                    "Ingrédients": [ingredients],
                    "Nutri-Score": [nutriscore]
                }
                st.table(product_info)
            else:
                st.error("Informations sur le produit non disponibles.")
        else:
            st.error("Aucun code-barres trouvé dans l'image.")
