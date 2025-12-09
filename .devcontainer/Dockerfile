FROM python:3.14-trixie

RUN mkdir /coco-expenses
WORKDIR /coco-expenses

RUN apt update
RUN apt install -y curl
# Backend
COPY backend/requirements.txt ./backend/requirements.txt

WORKDIR /coco-expenses/backend

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

# Frontend
WORKDIR /coco-expenses

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Create a script file sourced by both interactive and non-interactive bash shells
ENV BASH_ENV /root/.bash_env
RUN touch "${BASH_ENV}"
RUN echo '. "${BASH_ENV}"' >> ~/.bashrc

# Download and install nvm
RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | PROFILE="${BASH_ENV}" bash
RUN echo node > .nvmrc
RUN nvm install
RUN nvm install 24
RUN nvm use 24
RUN nvm alias default 24

RUN mkdir -p /coco-expenses/frontend/coco-expenses-v2-frontend
COPY ./frontend/coco-expenses-v2-frontend/package*.json /coco-expenses/frontend/coco-expenses-v2-frontend
WORKDIR /coco-expenses/frontend/coco-expenses-v2-frontend
RUN npm install

WORKDIR /coco-expenses
COPY . .

EXPOSE 5173