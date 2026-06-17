import firebase_admin
from firebase_admin import credentials, firestore

def conectar_firebase():
    try:
        # Verifica si Firebase ya se inició para no duplicar la conexión
        if not firebase_admin._apps:
            cred = credentials.Certificate("firebase-clave.json")
            firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception as e:
        print(f"❌ Error al conectar con Firebase Cloud: {e}")
        return None

def inicializar_datos_prueba():
    db = conectar_firebase()
    if db:
        print("🟢 ¡Conexión exitosa a Firestore Database!")
        
        # 🧰 INVENTARIO DE HERRAMIENTAS REAL DE PRUEBA
        db.collection("inventario").document("prod_1").set({
            "nombre": "Taladro Inalámbrico DeWalt 20V",
            "cantidad": 3,
            "precio": 1850.00,
            "categoria": "Herramientas Eléctricas"
        })
        
        db.collection("inventario").document("prod_2").set({
            "nombre": "Juego de Llaves Alen Stanley",
            "cantidad": 5,
            "precio": 320.00,
            "categoria": "Herramientas Manuales"
        })
        
        print("✨ ¡Inventario de herramientas sincronizado en la nube de Firebase!")

if __name__ == '__main__':
    inicializar_datos_prueba()