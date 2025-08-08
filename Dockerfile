# Usar una imagen base oficial de Python
FROM python:3.11-slim

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar el archivo de dependencias primero para aprovechar el cache de Docker
COPY requirements.txt .

# Instalar las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el código de la aplicación al directorio de trabajo
COPY . .

# Exponer el puerto en el que FastAPI se ejecutará
EXPOSE 8000

# Comando para ejecutar la aplicación cuando el contenedor se inicie
# El host 0.0.0.0 es necesario para que sea accesible desde fuera del contenedor
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]