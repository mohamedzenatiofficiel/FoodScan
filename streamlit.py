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
    """Récupère les informations d'un produit depuis OpenFoodFacts."""
    url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()

        if data['status'] == 0:
            return 'Produit non trouvé.', None, None, None

        product = data['product']
        name = product.get('product_name', 'Nom non disponible')
        ingredients = product.get('ingredients_text', 'Ingrédients non disponibles')
        nutriscore = product.get('nutriscore_grade', 'Nutri-Score non disponible')
        categories = product.get('categories')

        return name, ingredients, nutriscore, categories
    else:
        return 'Erreur lors de la récupération des données.', None, None, None


def get_alternative_products(categories, current_score, limit=3):
    """Retourne une liste d'alternatives plus saines basées sur la catégorie."""
    if not categories:
        return []

    category = categories.split(',')[0].strip().lower().replace(' ', '-')
    if not category:
        return []

    url = (
        f"https://world.openfoodfacts.org/category/{category}.json"
        f"?fields=product_name,nutriscore_grade&sort_by=nutriscore_grade"
    )
    try:
        response = requests.get(url)
    except Exception:
        return []

    if response.status_code != 200:
        return []

    data = response.json()
    products = data.get('products', [])

    alternatives = []
    for p in products:
        name = p.get('product_name')
        score = p.get('nutriscore_grade')
        if not name or not score:
            continue
        if current_score and score.lower() < current_score.lower():
            alternatives.append({'Nom': name, 'Nutri-Score': score})
        if len(alternatives) >= limit:
            break

    return alternatives

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
            name, ingredients, nutriscore, categories = get_product_info(barcode_data)

            if name is not None and not name.startswith("Erreur") and not name.startswith("Produit"):
                # Création du tableau
                product_info = {
                    "Nom du produit": [name],
                    "Ingrédients": [ingredients],
                    "Nutri-Score": [nutriscore]
                }
                st.table(product_info)

                alternatives = get_alternative_products(categories, nutriscore)
                if alternatives:
                    st.markdown("### Alternatives plus saines")
                    st.table(alternatives)
                else:
                    st.info("Aucune alternative plus saine trouvée ou catégorie absente.")
            else:
                st.error("Produit non trouvé ou erreur lors de la récupération des données.")
        else:
            st.error("Aucun code-barres trouvé dans l'image.")
