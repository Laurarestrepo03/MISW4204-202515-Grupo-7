#!/bin/bash
yes | sudo apt update
yes | sudo apt install apache2
echo "<p>Hello world!</p>" > /var/www/html/index.html
yes | sudo systemctl restart apache2
yes | sudo apt-get update
yes | sudo apt install apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
yes | sudo apt update
yes | sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
git clone https://github.com/Laurarestrepo03/MISW4204-202515-Grupo-7.git  /home/ubuntu/app
cd /home/ubuntu/app
cp docker_worker/Dockerfile .
cp docker_worker/.dockerignore .
cat <<EOF > .env
POSTGRES_DB=
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_HOST=
S3_BUCKET=
SQS_URL=
QUEUE_NAME=
EOF
yes | sudo docker build -t anb-worker .
yes | sudo docker run -d --name worker-background anb-worker

