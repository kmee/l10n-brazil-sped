# PVA of the Receita Federal in a headless X server. Built by imagem.sh from
# the official installer (checked against instaladores.csv); the image stays
# on the machine that built it and is never pushed to a registry.
FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8
RUN dpkg --add-architecture i386 && apt-get update && apt-get install -y --no-install-recommends \
    openjdk-17-jre xvfb xdotool imagemagick x11-utils \
    libxext6 libxrender1 libxtst6 libxi6 libxrandr2 libfreetype6 fontconfig fonts-liberation fonts-dejavu \
    libc6:i386 libstdc++6:i386 libaio1 libncurses5 libtinfo5 \
    poppler-utils procps python3 python3-fonttools \
 && rm -rf /var/lib/apt/lists/*
COPY fix_arial.py /tmp/fix_arial.py
RUN mkdir -p /usr/share/fonts/truetype/arial && python3 /tmp/fix_arial.py \
 && rm /tmp/fix_arial.py && fc-cache -f && fc-list | grep -q "Arial"
COPY instalador.sh /tmp/instalador.sh
ENV INSTALL4J_JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
RUN chmod +x /tmp/instalador.sh && /tmp/instalador.sh -q -dir /opt/pva -overwrite \
 && rm -f /tmp/instalador.sh && ls /opt/pva
# the embedded database of the PVA refuses to run as root
RUN useradd -m -u 1000 pva && chown -R pva:pva /opt/pva
USER pva
WORKDIR /home/pva
