minikube start --memory=4096 --cpus=8 --disk-size=40G 

echo "=========================================================="
echo "Minikube started successfully."
echo ""
echo "To enable external access to LoadBalancer services,"
echo "please run the following command in a separate terminal:"
echo ""
echo "    sudo minikube tunnel"
echo ""
echo "This command requires sudo privileges and will continue"
echo "running until you terminate it with Ctrl+C."
echo "=========================================================="