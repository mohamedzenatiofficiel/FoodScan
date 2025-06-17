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
    """Retrieve product information from OpenFoodFacts using the barcode.

    Returns:
        name (str or None): Product name or ``None`` if the barcode is invalid
            or an API error occurs.
        ingredients (str or None): Product ingredients or ``None`` if the
            barcode is invalid or an API error occurs.
        nutriscore (str or None): Nutri-Score grade or ``None`` if the barcode
            is invalid or an API error occurs.
        categories (str or None): Comma separated categories or ``None`` if not
            available.
        tags (list or None): List of category tags (``categories_tags`` or
            ``categories_hierarchy``) when present.
    """
    url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()

        if data.get('status') == 0:
            return 'Produit non trouvé.', None, None, None, None

        product = data.get('product', {})
        name = product.get('product_name', 'Nom non disponible')
        ingredients = product.get('ingredients_text', 'Ingrédients non disponibles')
        nutriscore = product.get('nutriscore_grade', 'Nutri-Score non disponible')

        categories = product.get('categories', '')
        tags = product.get('categories_tags') or product.get('categories_hierarchy')
        return name, ingredients, nutriscore, categories, tags
    else:
        return 'Erreur lors de la récupération des données.', None, None, None, None


def get_better_products(categories, nutriscore, tags=None):
    """Return a list of similar products with a better Nutri-Score.

    ``tags`` should be the list from ``categories_tags`` or ``categories_hierarchy``
    if available. The most specific tag (last element) is preferred for the
    search.
    """
    nutri_order = ["a", "b", "c", "d", "e"]

    if (not categories and not tags) or nutriscore not in nutri_order:
        return []

    if tags:
        category = tags[-1]
    else:
        category = categories.split(",")[0].strip()
    current_index = nutri_order.index(nutriscore)
    better_grades = nutri_order[:current_index]

    results = []
    for grade in better_grades:
        url = (
            "https://world.openfoodfacts.org/cgi/search.pl?"
            f"search_terms=&tagtype_0=categories&tag_contains_0=contains&tag_0={category}"
            f"&tagtype_1=nutriscore_grade&tag_contains_1=contains&tag_1={grade}&page_size=5&json=1"
        )
        resp = requests.get(url)
        if resp.status_code == 200:
            data = resp.json()
            products = [p.get("product_name") for p in data.get("products", []) if p.get("product_name")]
            results.extend(products)

    return results

# Configuration de l'interface Streamlit
st.title("Scanner de code-barres et récupération d'informations sur le produit")

# Choix de la source d'image
source = st.radio(
    "Sélectionnez la source de l'image",
    ("Upload de fichier", "Scanner avec la webcam"),
)

image = None

if source == "Upload de fichier":
    uploaded_file = st.file_uploader(
        "Chargez une image contenant un code-barres", type=["png", "jpg", "jpeg"]
    )
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Image chargée", use_column_width=True)
elif source == "Scanner avec la webcam":
    camera_file = st.camera_input("Scanner avec la webcam")
    if camera_file is not None:
        image = Image.open(camera_file)
        st.image(image, caption="Image capturée", use_column_width=True)

if image is not None:
    if st.button("Scanner le code-barres"):
        barcode_data = read_barcode_from_image(image)

        if barcode_data:
            st.success(f"Code-barres détecté: {barcode_data}")
            name, ingredients, nutriscore, categories, tags = get_product_info(barcode_data)

            if ingredients is not None:
                # Création du tableau
                product_info = {
                    "Nom du produit": [name],
                    "Ingrédients": [ingredients],
                    "Nutri-Score": [nutriscore],
                }
                st.table(product_info)

                suggestions = get_better_products(categories, nutriscore, tags)
                if suggestions:
                    st.success("Produits similaires de meilleure qualité :")
                    for s in suggestions:
                        st.write(f"- {s}")
            else:
                st.error(name)
        else:
            st.error("Aucun code-barres trouvé dans l'image.")
