from django import template

register = template.Library()


@register.filter
def medida_valor(objeto, campo):
    # Solo expone los campos de medida previstos, nunca atributos arbitrarios.
    if campo in ["cuello", "hombro", "pecho", "cintura", "cadera", "largo_manga", "largo_pantalon", "largo_prenda"]:
        return getattr(objeto, campo)
    return None


@register.filter
def etiqueta_medida(campo):
    return campo.replace("_", " ").capitalize()
