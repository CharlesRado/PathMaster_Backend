import firebase_admin
from firebase_admin import credentials, firestore

# Initialise Firebase
cred = credentials.Certificate("config/pathmaster-327b2-firebase-adminsdk-fbsvc-708e63f7c0.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Catégories à supprimer
categories_to_delete = ["LLM", "Robotics", "Both"]

# Supprimer les documents avec ces catégories
def delete_by_categories():
    for category in categories_to_delete:
        docs = db.collection("articles").where("category", "==", category).stream()
        count = 0
        for doc in docs:
            db.collection("articles").document(doc.id).delete()
            count += 1
        print(f"🗑️ Supprimé {count} articles avec la catégorie: {category}")

if __name__ == "__main__":
    delete_by_categories()
