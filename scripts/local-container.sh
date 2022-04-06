docker rm -f qt-app &2>/dev/null
docker build -t qt-app -f Dockerfile .
docker run --name qt-app --env-file local.env -p 5000:5000 -d qt-app:latest