# Usa una imagen oficial de Python como base
FROM python:3.9-slim

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia el archivo de requerimientos primero para cachear las capas
COPY requirements.txt requirements.txt

# Instala las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código de tu aplicación
COPY . .

# Expone el puerto en el que correrá la aplicación (Hugging Face lo gestiona)
EXPOSE 7860

# El comando para iniciar tu aplicación Flask usando Gunicorn (un servidor de producción)
CMD ["gunicorn", "--bind", "0.0.0.0:7860", "app:app"]
