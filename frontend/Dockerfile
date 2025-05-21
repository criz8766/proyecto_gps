# Etapa de construcción
FROM node:18-alpine AS build

WORKDIR /app

# Copiar package.json y package-lock.json (o yarn.lock)
# Esto aprovecha el caché de Docker si las dependencias no cambian
COPY package.json ./
COPY package-lock.json ./
# Si usas yarn, en lugar de package-lock.json, copia yarn.lock:
# COPY yarn.lock ./

# Instalar dependencias
RUN npm install
# Si usas yarn:
# RUN yarn install

# Copiar el resto del código de la aplicación
COPY . .

# Construir la aplicación para producción
RUN npm run build
# Si usas yarn:
# RUN yarn build

# Etapa de producción (servir los archivos estáticos con Nginx)
FROM docker.io/library/nginx:1.25-alpine

# Copiar los archivos construidos desde la etapa de 'build'
# El resultado de 'npm run build' en Create React App usualmente está en la carpeta 'build'
COPY --from=build /app/build /usr/share/nginx/html

# (Opcional) Copiar una configuración personalizada de Nginx si la necesitas
# COPY nginx.conf /etc/nginx/conf.d/default.conf

# Exponer el puerto en el que Nginx escucha por defecto
EXPOSE 80

# Comando para iniciar Nginx
CMD ["nginx", "-g", "daemon off;"]
