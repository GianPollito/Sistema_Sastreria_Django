from django import forms
from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError


class EmpleadoForm(forms.Form):
    usuario = forms.CharField(max_length=150)
    nombre = forms.CharField(max_length=150)
    apellido = forms.CharField(max_length=150, required=False)
    correo = forms.EmailField(required=False)
    telefono = forms.CharField(max_length=30, required=False)
    rol = forms.ModelChoiceField(queryset=Group.objects.filter(name__in=["Administrador", "Recepcionista", "Sastre"]))
    clave = forms.CharField(label="Contraseña (déjala vacía para conservar la actual)", required=False, widget=forms.PasswordInput)
    activo = forms.BooleanField(required=False, initial=True)

    def __init__(self, *args, empleado=None, **kwargs):
        self.empleado = empleado
        super().__init__(*args, **kwargs)

    def clean(self):
        datos = super().clean()
        usuarios = get_user_model().objects.filter(username=datos.get("usuario", ""))
        if self.empleado:
            usuarios = usuarios.exclude(pk=self.empleado.usuario_id)
        if usuarios.exists():
            self.add_error("usuario", "Ese nombre de usuario ya existe.")
        if not self.empleado and not datos.get("clave"):
            self.add_error("clave", "Define una contraseña para el empleado.")
        if datos.get("clave"):
            usuario = get_user_model()(username=datos.get("usuario"), first_name=datos.get("nombre"), last_name=datos.get("apellido"), email=datos.get("correo"))
            try:
                password_validation.validate_password(datos["clave"], usuario)
            except ValidationError as error:
                self.add_error("clave", error)
        return datos
