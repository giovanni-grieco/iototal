kubectl delete pod --field-selector=status.phase==Succeeded
kubectl delete pod --field-selector=status.phase==Failed