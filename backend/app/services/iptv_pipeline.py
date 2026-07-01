class IPTVPipeline:
    @staticmethod
    def limpiar_lista_canales(raw_data):
        """Limpia y normaliza los nombres y URLs de los canales."""
        lista_procesada = []
        for item in raw_data:
            canal = {
                "nombre": item.get("title", "").strip(),
                "url": item.get("url", "").strip(),
                "grupo": item.get("group-title", "General"),
                "logo": item.get("tvg-logo", None)
            }
            lista_procesada.append(canal)
        return lista_procesada

    @staticmethod
    def filtrar_por_categoria(lista, categoria):
        """Filtra los canales por categoría."""
        return [c for c in lista if c["grupo"].lower() == categoria.lower()]