FROM python:3.10.14

USER root

WORKDIR /app
ARG USER_HOST
ARG USER_EMAIL

ENV USERNAME=$USER_HOST
ENV EMAIL=$USER_EMAIL

# Install basic CLI tools
RUN apt-get update -y && apt-get install -y \
                         gnupg \
                         wget \
                         git \
                         openssh-client \
                         graphviz

# Install DVC
RUN wget \
       https://dvc.org/deb/dvc.list \
       -O /etc/apt/sources.list.d/dvc.list
RUN wget -qO - https://dvc.org/deb/iterative.asc | gpg --dearmor > packages.iterative.gpg
RUN install -o root -g root -m 644 packages.iterative.gpg /etc/apt/trusted.gpg.d/
RUN rm -f packages.iterative.gpg
RUN apt update -y && apt install -y dvc

# ZSH
RUN apt-get update && apt-get install -y zsh
RUN apt-get install -y wget
# Uses "robbyrussell" theme (original Oh My Zsh theme), with no plugins
RUN sh -c "$(wget -O- https://github.com/deluan/zsh-in-docker/releases/download/v1.1.5/zsh-in-docker.sh)" -- \
    -t aussiegeek
# customizations
RUN apt-get install figlet -y
RUN echo "alias ll='ls -l'" >> ~/.zshrc

RUN echo "figlet DATASET-IA" >> ~/.zshrc
RUN echo "figlet DATASET-IA" >> ~/.bashrc

RUN pip install pandas
RUN pip install sphinx

RUN pip install glob2 dvc boto3
RUN pip install "dvc[s3]"
RUN pip install tqdm glob2


RUN git config --global user.email "$EMAIL"
RUN git config --global user.name "$USERNAME"

RUN curl -O https://dl.min.io/client/mc/release/linux-amd64/mc
RUN chmod +x mc
RUN mv mc /usr/local/bin/

# =================================================
#  Añadir alias para scripts de DVC
# =================================================
RUN echo '\n# --- Alias para scripts de DVC ---' >> /root/.zshrc && \
    echo "alias dvc_upload='bash /app/src/scripts/upload/dvc_up.sh'" >> /root/.zshrc && \
    echo "alias dvc_inventory='python3 /app/src/scripts/upload/files_inventory.py'" >> /root/.zshrc && \
    echo "alias dvc_download_folder='bash /app/src/scripts/download/download_complete_folder.sh'" >> /root/.zshrc && \
    echo "alias dvc_download_file='python3 /app/src/scripts/download/download_some_file.py'" >> /root/.zshrc
RUN echo '\n# --- Alias para scripts de DVC ---' >> /root/.bashrc && \
    echo "alias dvc_upload='bash /app/src/scripts/upload/dvc_up.sh'" >> /root/.bashrc && \
    echo "alias dvc_inventory='python3 /app/src/scripts/upload/files_inventory.py'" >> /root/.bashrc && \
    echo "alias dvc_download_folder='bash /app/src/scripts/download/download_complete_folder.sh'" >> /root/.bashrc && \
    echo "alias dvc_download_file='python3 /app/src/scripts/download/download_some_file.py'" >> /root/.bashrc


# Copy the .dvc directory containing the remote configuration BEFORE adding the remote
WORKDIR /app/.dvc/
COPY .dvc/ /app/.dvc/

WORKDIR /app/.git/
COPY .git/ /app/.git/

WORKDIR /app/config
COPY config/ /app/config

WORKDIR /app/src
COPY src/ /app/src

RUN git config --global --add safe.directory /app && \
    git config --system --add safe.directory /app

WORKDIR /app/projects
