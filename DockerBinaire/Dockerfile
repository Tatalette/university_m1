FROM php:8.2-cli

# Installation des extensions PHP nécessaires
RUN docker-php-ext-install sockets

# Installation de Composer
COPY --from=composer:latest /usr/bin/composer /usr/bin/composer

# Définition du répertoire de travail
WORKDIR /var/www/html

# Copie des fichiers sources
COPY src/ /var/www/html/
COPY bin/ /var/www/bin/

# Optionnel : installation d'outils utiles
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    net-tools \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*