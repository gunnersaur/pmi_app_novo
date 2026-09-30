def estilo_linha(row):
    resultado = str(row["Resultado"]).upper()

    if "OK" in resultado:
        return ["background-color: #d4edda; color: #155724"] * len(row)

    elif "ATENÇÃO" in resultado or "ATENCAO" in resultado:
        return ["background-color: #fff3cd; color: #856404"] * len(row)

    elif "VERIFICAR" in resultado or "DIVERGÊNCIA" in resultado or "DIVERGENCIA" in resultado:
        return ["background-color: #f8d7da; color: #721c24"] * len(row)

    elif "NÃO LOCALIZADO" in resultado or "NAO LOCALIZADO" in resultado:
        return ["background-color: #e2e3e5; color: #383d41"] * len(row)

    return [""] * len(row)
