from flask import Flask, render_template, request, jsonify
from database import conectar_firebase

app = Flask(__name__)

# 1. RUTA PRINCIPAL: Carga la pantalla de la interfaz
@app.route('/')
def home():
    return render_template('index.html')

# 2. RUTA PARA CONSULTAR EL INVENTARIO DESDE GOOGLE CLOUD
@app.route('/get_inventario', methods=['GET'])
def get_inventario():
    db = conectar_firebase()
    if not db:
        return jsonify({"success": False, "error": "No hay conexión con la base de datos."})
    try:
        productos_ref = db.collection("inventario").stream()
        lista = []
        for p in productos_ref:
            d = p.to_dict()
            lista.append({
                "id": p.id,
                "nombre": d.get("nombre", "Sin nombre"),
                "cantidad": d.get("cantidad", 0),
                "precio": d.get("precio", 0)
            })
        return jsonify({"success": True, "data": lista})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# 3. RUTA PARA CONSULTAR LOS TICKETS DESDE GOOGLE CLOUD
@app.route('/get_tickets', methods=['GET'])
def get_tickets():
    db = conectar_firebase()
    if not db:
        return jsonify({"success": False, "error": "No hay conexión con la base de datos."})
    try:
        tickets_ref = db.collection("tickets").stream()
        lista = []
        for t in tickets_ref:
            d = t.to_dict()
            lista.append({
                "id": t.id,
                "titulo": d.get("modulo_afectado", "Entrega"),
                "telefono": d.get("telefono", "N/A"),
                "producto_nombre": d.get("descripcion_problema", "").split("|")[0].replace("Producto:", "").strip() if "|" in d.get("descripcion_problema", "") else d.get("descripcion_problema", ""),
                "cantidad_pedida": d.get("cantidad", 1),
                "total_cobro": d.get("precio", 0),
                "estado": d.get("estado", "Pendiente")
            })
        return jsonify({"success": True, "data": lista})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# 4. RUTA DEL CHATBOT: Procesa comandos y guarda en Firebase con categoría corregida
@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    mensaje_usuario = data.get("message", "").strip()
    mensaje_minusculas = mensaje_usuario.lower()
    db = conectar_firebase()
    
    if not db:
        return jsonify({"reply": "⚠️ Error: No se pudo conectar con el servidor central de Firebase."})

    # A) COMANDO: AÑADIR PRODUCTO
    if mensaje_minusculas.startswith("añadir:") or mensaje_minusculas.startswith("anadir:"):
        try:
            texto_puro = mensaje_usuario[7:].strip()
            partes = [p.strip() for p in texto_puro.split(",")]
            
            nombre = partes[0]
            cantidad = int(partes[1])
            precio = float(partes[2].replace("$", ""))
            
            # Asignación dinámica de categoría según el artículo real
            nombre_min = nombre.lower()
            if "gancho" in nombre_min or "multitool" in nombre_min or "cable" in nombre_min or "taladro" in nombre_min:
                categoria_real = "Herramientas y Materiales"
            else:
                categoria_real = "General"
            
            # Guardamos en Firebase Cloud
            nueva_ref = db.collection("inventario").document()
            nueva_ref.set({
                "nombre": nombre,
                "cantidad": cantidad,
                "precio": precio,
                "categoria": categoria_real
            })
            return jsonify({"reply": f"✅ He añadido <b>{nombre}</b> a la colección de Firebase bajo la categoría <b>'{categoria_real}'</b>."})
        except Exception as e:
            return jsonify({"reply": f"❌ Error al guardar en la nube: {e}"})

    # B) COMANDO: REGISTRAR TICKET CON COBRO AUTOMÁTICO
    elif mensaje_minusculas.startswith("ticket:"):
        try:
            texto_puro = mensaje_usuario[7:].strip()
            partes = [p.strip() for p in texto_puro.split(",")]
            
            lugar = partes[0]
            telefono = partes[1]
            producto_buscado = partes[2]
            cantidad_pedida = int(partes[3])
            
            # Buscar el precio en la nube para calcular el total
            productos_ref = db.collection("inventario").stream()
            precio_producto = 0
            nombre_real = producto_buscado
            
            for p in productos_ref:
                d = p.to_dict()
                if d.get("nombre", "").lower() == producto_buscado.lower():
                    precio_producto = d.get("precio", 0)
                    nombre_real = d.get("nombre")
                    break
            
            total_calculado = precio_producto * cantidad_pedida
            
            # Guardamos el ticket estructurado en Firebase
            nuevo_ticket = db.collection("tickets").document()
            nuevo_ticket.set({
                "modulo_afectado": lugar,
                "telefono": telefono,
                "descripcion_problema": f"Producto: {nombre_real} | Cantidad: {cantidad_pedida}",
                "cantidad": cantidad_pedida,
                "precio": total_calculado,
                "prioridad": "Media",
                "estado": "Pendiente"
            })
            return jsonify({"reply": f"🎫 <b>¡Ticket Creado!</b> Para la entrega en <b>${lugar}</b>. Cobro automático calculado en la nube: <b>${totalCalculado}</b>."})
        except Exception as e:
            return jsonify({"reply": f"❌ Error al procesar el ticket en la nube: {e}"})
            
    return jsonify({"reply": "🤖 Comando no reconocido. Escribe 'hola' para consultar los formatos."})

# 5. RUTAS PARA ELIMINAR DIRECTAMENTE DESDE LOS BOTONES (🗑️)
@app.route('/eliminar_producto/<id>', methods=['DELETE'])
def eliminar_producto(id):
    try:
        db = conectar_firebase()
        db.collection("inventario").document(id).delete()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/eliminar_ticket/<id>', methods=['DELETE'])
def eliminar_ticket(id):
    try:
        db = conectar_firebase()
        db.collection("tickets").document(id).delete()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    app.run(port=8080, debug=True)