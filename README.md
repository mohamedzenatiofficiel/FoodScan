# FoodScan

Cette application Streamlit permet de lire un code-barres depuis une image puis d'afficher les informations du produit depuis OpenFoodFacts.

## Optimisation du cache

La fonction `get_product_info` utilise désormais le décorateur `@st.cache_data` (ou `@st.experimental_memo` selon la version de Streamlit). Cette mise en cache évite d'effectuer plusieurs requêtes réseau pour un même code‑barres : si le même identifiant est scanné à nouveau, les données sont récupérées directement depuis le cache.

Pour exécuter les tests :

```bash
pip install -r requirements.txt
pytest
```
