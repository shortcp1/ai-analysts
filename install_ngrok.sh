#!/bin/bash

echo "Downloading Ngrok..."
curl -s https://bin.equinox.io/c/4VmDzA7iaHb/ngrok-stable-linux-amd64.zip -o ngrok-stable-linux-amd64.zip

echo "Unzipping Ngrok..."
unzip ngrok-stable-linux-amd64.zip

echo "Installing Ngrok to /usr/local/bin..."
sudo mv ngrok /usr/local/bin/

echo "Cleaning up downloaded zip file..."
rm ngrok-stable-linux-amd64.zip

echo "Verifying Ngrok installation..."
ngrok version

echo "Ngrok installation complete."
echo "Remember to authenticate Ngrok with your authtoken: ngrok authtoken <YOUR_AUTHTOKEN>"
echo "Then, start the tunnel: ngrok http 8000"