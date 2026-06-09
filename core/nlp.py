import re
import unicodedata


def normalizar(texto):
    texto = texto.lower().strip()
    texto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


def contiene_frase(texto, frases):
    texto = normalizar(texto)
    return any(re.search(rf"\b{re.escape(normalizar(frase))}\b", texto) for frase in frases)


def parsear_numeros(texto):
    return [float(x) for x in re.findall(r"[-+]?\d*\.?\d+", texto)]


def parsear_restriccion(texto):
    texto_norm = texto.strip()
    if "<=" in texto_norm:
        signo = "<="
        partes = texto_norm.split("<=")
    elif ">=" in texto_norm:
        signo = ">="
        partes = texto_norm.split(">=")
    elif "=" in texto_norm:
        signo = "="
        partes = texto_norm.split("=")
    else:
        return None
    if len(partes) < 2:
        return None
    coefs = parsear_numeros(partes[0])
    rhs = parsear_numeros(partes[1])
    if not coefs or not rhs:
        return None
    return (coefs, signo, rhs[0])


def detectar_intencion(texto):
    texto_norm = normalizar(texto)

    if re.fullmatch(r"(opcion\s*)?1[\.\)]?", texto_norm):
        return "clasificar"
    if re.fullmatch(r"(opcion\s*)?2[\.\)]?", texto_norm):
        return "resolver"
    if re.fullmatch(r"(opcion\s*)?3[\.\)]?", texto_norm):
        return "explicar"

    if contiene_frase(texto, ["hola", "buenas", "que tal", "saludos"]):
        return "saludo"
    if contiene_frase(
        texto,
        ["clasificar", "diagnostico", "que metodo", "cual metodo", "recomendar", "identificar", "opcion 1"],
    ):
        return "clasificar"
    if contiene_frase(
        texto,
        ["resolver", "ejercicio", "guia", "como se hace", "pasos", "resolucion", "opcion 2"],
    ):
        return "resolver"
    if contiene_frase(
        texto,
        ["explicar", "concepto", "que es", "entender", "definicion", "teoria", "opcion 3"],
    ):
        return "explicar"
    return "desconocido"


def detectar_si_no(texto):
    if contiene_frase(texto, ["si", "claro", "por supuesto", "dale", "ok", "correcto", "afirmativo"]):
        return "si"
    if contiene_frase(texto, ["no", "negativo", "para nada", "incorrecto"]):
        return "no"
    return None
