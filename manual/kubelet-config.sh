oc label mcp master box1-pod-density=enabled

cat <<'EOF' | oc apply -f -
apiVersion: machineconfiguration.openshift.io/v1
kind: KubeletConfig
metadata:
  name: box1-pod-density
spec:
  machineConfigPoolSelector:
    matchLabels:
      box1-pod-density: enabled
  kubeletConfig:
    maxPods: 400
    podsPerCore: 0
EOF
