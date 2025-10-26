from flask import Flask, render_template, request, jsonify, session
import difflib

app = Flask(__name__)
app.secret_key = "clave_secreta_chatbot"


temas = {
    "alimentacion": {
        "descripcion": "Consejos sobre nutrición, pastos y suplementos del ganado.",
        "preguntas": {
            "cuanta comida necesita una vaca": "Un bovino adulto consume entre el 2.5% y el 3% de su peso corporal en materia seca al día.",
            "que come el ganado en epoca seca": "Durante la época seca se recomienda usar ensilaje, heno o bloques nutricionales.",
            "que sales minerales se usan": "Las sales minerales con fósforo, calcio y sodio son esenciales para el ganado.",
        },
    },
    "reproduccion": {
        "descripcion": "Todo sobre inseminación, celo y partos.",
        "preguntas": {
            "que es la inseminacion artificial": "La inseminación artificial mejora la genética y permite controlar los tiempos de parto.",
            "cada cuanto se puede inseminar una vaca": "Después del parto, se recomienda inseminar entre los 60 y 90 días, según la condición corporal.",
            "como detectar el celo": "Observa inquietud, monta a otras vacas y presenta moco transparente. Esos son signos de celo.",
        },
    },
    "enfermedades": {
        "descripcion": "Información sobre sanidad, vacunación y prevención.",
        "preguntas": {
            "que vacunas necesita el ganado": "Depende de la región, pero las más comunes son contra brucelosis, fiebre aftosa y carbunco.",
            "como prevenir la mastitis": "Mantén una buena higiene en el ordeño y revisa los pezones con regularidad.",
            "sintomas de brucelosis": "Abortos repetidos, retención de placenta y fiebre intermitente son síntomas comunes.",
        },
    },
    "razas": {
        "descripcion": "Razas lecheras, de carne y doble propósito.",
        "preguntas": {
            "que razas son buenas para leche": "Las razas Holstein, Jersey y Pardo Suizo son las más lecheras.",
            "que razas son buenas para carne": "Brahman, Angus y Charolais son razas muy productivas en carne.",
            "que raza sirve para doble proposito": "El Gyr cruzado o Simmental son excelentes para doble propósito 🐂.",
        },
    },
    "manejo": {
        "descripcion": "Prácticas de manejo, instalaciones y bienestar animal.",
        "preguntas": {
            "como mejorar el bienestar animal": "Proporciona sombra, agua limpia y espacio suficiente para moverse.",
            "que tipo de cercas usar": "Las cercas eléctricas son efectivas y económicas para el manejo del ganado.",
            "como manejar el estiércol": "El estiércol puede compostarse para usarlo como fertilizante natural en pasturas.",
        },
    },
    

}


cuestionarios = {
    "alimentacion": [
        "¿Qué tipo de pasto tienes en tu finca?",
        "¿Con qué frecuencia alimentas al ganado?",
        "¿Usas suplementos o sales minerales?"
    ],
    "reproduccion": [
        "¿Qué sistema de reproducción usas: natural o inseminación artificial?",
        "¿Cuántas vacas manejas por toro?",
        "¿Llevas registro de servicios y partos?"
    ]
}

def generar_conclusion(tema, respuestas):
    if tema == "alimentacion":
        pasto, frecuencia, suplementos = respuestas
        conclusion = "Según tus respuestas sobre alimentación:\n"
        conclusion += f"- Tipo de pasto: {pasto}\n"
        conclusion += f"- Frecuencia de alimentación: {frecuencia}\n"
        conclusion += f"- Suplementos: {suplementos}\n\n"
        if "escaso" in frecuencia or "poco" in frecuencia:
            conclusion += "Recomendación: Aumenta la frecuencia de alimentación para mejorar la ganancia de peso."
        elif "sí" in suplementos or "minerales" in suplementos:
            conclusion += "Excelente, tu ganado está recibiendo suplementación adecuada."
        else:
            conclusion += "Considera añadir sales minerales para mantener la salud del ganado."
        return conclusion
    elif tema == "reproduccion":
        sistema, cantidad, registro = respuestas
        conclusion = "Según tus respuestas sobre reproducción:\n"
        conclusion += f"- Sistema: {sistema}\n"
        conclusion += f"- Cantidad de vacas por toro: {cantidad}\n"
        conclusion += f"- Registro de servicios: {registro}\n\n"
        conclusion += "Recomendación: Mantener registros precisos ayuda a mejorar la fertilidad y productividad."
        return conclusion
    return "Gracias por tus respuestas, revisa tus prácticas para optimizar tu hato."


REGLAS_VETERINARIAS = {
    
    "Fiebre Aftosa": {
        "especie": "Bovino",
        "sintomas_requeridos": ["ampollas boca", "salivacion excesiva", "cojera fuerte"],
        "recomendacion": "ALERTA SANITARIA. Contactar inmediatamente a las autoridades veterinarias. Aislamiento estricto."
    },
    "Mastitis": {
        "especie": "Bovino",
        "sintomas_requeridos": ["ubre hinchada", "leche anormal"],
        "recomendacion": "Iniciar tratamiento de soporte y ordeño frecuente. Consultar veterinario."
    },
    "Neumonía Bovina": {
        "especie": "Bovino",
        "sintomas_requeridos": ["tos severa", "dificultad respiratoria", "fiebre"],
        "recomendacion": "Aislar al animal. Administrar antibióticos recetados y mejorar ventilación."
    },
    "Brucelosis": {
        "especie": "Bovino",
        "sintomas_requeridos": ["abortos", "retencion lacenta cronica"],
        "recomendacion": "Realizar pruebas serológicas. Enfermedad de control obligatorio."
    },
    "Cetosis (Acetonemia)": {
        "especie": "Bovino",
        "sintomas_requeridos": ["olor acetona", "perdida apetito", "postparto"],
        "recomendacion": "Suplemento energético oral o intravenoso. Revisar dieta."
    },
    "Timpanismo Agudo": {
        "especie": "Bovino",
        "sintomas_requeridos": ["abdomen inflado izq", "dificultad respiratoria grave"],
        "recomendacion": "Caso de emergencia. Administrar antiflatulentos o realizar punción de emergencia."
    },

   
    "Peste Porcina Clásica (PPC)": {
        "especie": "Porcino",
        "sintomas_requeridos": ["fiebre alta", "ataxia", "cianosis orejas"],
        "recomendacion": "ALERTA SANITARIA. Notificación inmediata a las autoridades."
    },
    "Erisipela": {
        "especie": "Porcino",
        "sintomas_requeridos": ["lesiones rombo", "fiebre alta"],
        "recomendacion": "Tratamiento con penicilina. Vacunación preventiva si hay brotes recurrentes."
    },
    "Enfermedad de Aujeszky": {
        "especie": "Porcino",
        "sintomas_requeridos": ["prurito intenso", "signos nerviosos", "vómitos"],
        "recomendacion": "Vacunación preventiva. No existe tratamiento."
    },
    "SRRP (PRRS)": {
        "especie": "Porcino",
        "sintomas_requeridos": ["fallas reproductivas", "tos seca"],
        "recomendacion": "Manejo estricto de bioseguridad. Vacunación y control de la ventilación."
    },
    "Diarrea Epidémica Porcina (DEP)": {
        "especie": "Porcino",
        "sintomas_requeridos": ["diarrea lechones severa", "alta mortalidad lechones"],
        "recomendacion": "Mantener calor y ofrecer electrolitos a lechones."
    },
    "Sarna Porcina": {
        "especie": "Porcino",
        "sintomas_requeridos": ["costras piel", "picazon intensa orejas"],
        "recomendacion": "Tratar con Ivermectina a todo el rebaño. Limpiar instalaciones."
    },

    
    "Cólico": {
        "especie": "Equino",
        "sintomas_requeridos": ["dolor abdominal", "pataleo constante", "intenta echarse"],
        "recomendacion": "EMERGENCIA VETERINARIA. Retirar alimento. Caminar al caballo."
    },
    "Laminitis (Infosura)": {
        "especie": "Equino",
        "sintomas_requeridos": ["cascos calientes dolor", "postura caracteristica sierra"],
        "recomendacion": "EMERGENCIA VETERINARIA. Aplicar frío en cascos."
    },
    "Influenza Equina": {
        "especie": "Equino",
        "sintomas_requeridos": ["tos aguda repentina", "secrecion nasal serosa", "fiebre"],
        "recomendacion": "Aislamiento inmediato (4 semanas). Reposo estricto."
    },
    "Tétanos": {
        "especie": "Equino",
        "sintomas_requeridos": ["rigidez muscular", "membrana nicitante expuesta", "herida profunda reciente"],
        "recomendacion": "EMERGENCIA VETERINARIA. Administrar antitoxina y antibióticos."
    },
    "Encefalomielitis Equina": {
        "especie": "Equino",
        "sintomas_requeridos": ["ataxia", "presion cabeza contra pared", "ceguera aparente"],
        "recomendacion": "Enfermedad viral grave. Aislamiento. Contactar autoridades sanitarias."
    },
    "Moquillo (Adenitis Equina)": {
        "especie": "Equino",
        "sintomas_requeridos": ["linfonodos inflamados garganta", "secrecion nasal purulenta", "fiebre"],
        "recomendacion": "Aislamiento. Aplicar calor en abscesos."
    }
}


def motor_de_inferencia(especie_animal, sintomas_reportados):
    diagnosticos = {}
    sintomas_set = set(sintomas_reportados)
    for enfermedad, regla in REGLAS_VETERINARIAS.items():
        if regla["especie"].lower() == especie_animal.lower():
            if set(regla["sintomas_requeridos"]).issubset(sintomas_set):
                diagnosticos[enfermedad] = regla["recomendacion"]
    return diagnosticos


def buscar_respuesta(pregunta_usuario):
    pregunta_usuario = pregunta_usuario.lower()
    mejor_similitud = 0
    respuesta = None

    for tema, datos in temas.items():
        for pregunta, resp in datos["preguntas"].items():
            similitud = difflib.SequenceMatcher(None, pregunta_usuario, pregunta).ratio()
            if similitud > mejor_similitud:
                mejor_similitud = similitud
                respuesta = resp

    if mejor_similitud > 0.6:
        return respuesta
    return None


@app.route("/")
def home():
    session.clear()
    return render_template("index.html")

@app.route("/reset", methods=["POST"])
def reset_chat():
    session.clear()
    temas_lista = "\n".join([f"• {t.capitalize()}: {v['descripcion']}" for t, v in temas.items()])
    saludo = f"¡Hola ganadero! 🐮 Chat reiniciado.\n\n{temas_lista}\n\nTambién puedes iniciar cuestionario o diagnóstico veterinario."
    return jsonify({"response": saludo})

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True)
    msg = data.get("message", "").lower().strip()

   
    if "cuestionario_activo" in session:
        tema = session["cuestionario_activo"]
        index = session["cuestionario_index"]
        respuestas = session["respuestas_cuestionario"]

        respuestas.append(msg)
        session["respuestas_cuestionario"] = respuestas
        index += 1

        if index < len(cuestionarios[tema]):
            session["cuestionario_index"] = index
            return jsonify({"response": cuestionarios[tema][index]})
        else:
            conclusion = generar_conclusion(tema, respuestas)
            session.pop("cuestionario_activo")
            session.pop("cuestionario_index")
            session.pop("respuestas_cuestionario")
            return jsonify({"response": f"✅ Gracias por tus respuestas.\n\n{conclusion}"})

    
    if "cuestionario" in msg:
        for tema in cuestionarios.keys():
            if tema in msg:
                session["cuestionario_activo"] = tema
                session["cuestionario_index"] = 0
                session["respuestas_cuestionario"] = []
                return jsonify({"response": cuestionarios[tema][0]})

    
    if "diagnostico" in msg or "diagnóstico" in msg:
        session["fase"] = "diagnostico"
        return jsonify({"response": "¿Qué especie deseas diagnosticar? (Bovino 🐄 , Porcino 🐷, Equino 🐎)"})

    
    if "fase" in session and session["fase"] == "diagnostico":
        
        if "especie" not in session:
            especies_validas = ["bovino", "porcino", "equino"]
            if msg in especies_validas:
                session["especie"] = msg
                
                sintomas = []
                for regla in REGLAS_VETERINARIAS.values():
                    if regla["especie"].lower() == msg:
                        sintomas.extend(regla["sintomas_requeridos"])
                session["sintomas_posibles"] = list(set(sintomas))
                session["sintoma_index"] = 0
                session["sintomas"] = []
                return jsonify({"response": f"Responde con 'sí' o 'no'.\n¿El animal presenta: {session['sintomas_posibles'][0]}?"})
            else:
                return jsonify({"response": "Especie no válida. Elige: Bovino, Porcino o Equino."})
        else:
            
            index = session["sintoma_index"]
            if msg in ["sí", "si"]:
                session["sintomas"].append(session["sintomas_posibles"][index])
            index += 1
            if index < len(session["sintomas_posibles"]):
                session["sintoma_index"] = index
                return jsonify({"response": f"¿El animal presenta: {session['sintomas_posibles'][index]}?"})
            else:
                resultados = motor_de_inferencia(session["especie"], session["sintomas"])
                session.clear()
                if resultados:
                    textos = "\n".join([f"- {enf}: {rec}" for enf, rec in resultados.items()])
                    return jsonify({"response": f"✅ Diagnóstico preliminar:\n{textos}"})
                else:
                    return jsonify({"response": "❌ No se encontró un diagnóstico claro."})

    
    if "inicio" not in session:
        session["inicio"] = True
        temas_lista = "\n".join([f"• {t.capitalize()}: {v['descripcion']}" for t, v in temas.items()])
        return jsonify({"response": f"¡Hola ganadero! 🐮 ¿Sobre qué tema quieres hablar hoy?\n\n{temas_lista}\n\nTambién puedes iniciar cuestionario o diagnóstico veterinario."})
    
    if "adios" in msg or "gracias" in msg or "hasta luego" in msg or "chao" in msg :
        session.clear()
        return jsonify({"response": "¡Hasta luego! Si necesitas más ayuda, aquí estaré."})


    
    for tema in temas.keys():
        if tema in msg:
            preguntas = "\n".join([f"• {p.capitalize()}" for p in temas[tema]["preguntas"].keys()])
            return jsonify({"response": f"Perfecto, hablemos sobre {tema}.\n¿Qué te gustaría saber?\n\n{preguntas}"})

    
    respuesta = buscar_respuesta(msg)
    if respuesta:
        return jsonify({"response": respuesta})

    return jsonify({"response": "No entendí muy bien. "})

    

if __name__ == "__main__":
    app.run(debug=True)
