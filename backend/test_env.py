
import sys
print(f"Python: {sys.version}")

try:
    import torch
    print(f"Torch: {torch.__version__}")
    x = torch.rand(5, 3)
    print("Torch tensor created successfully.")
except ImportError as e:
    print(f"Torch Error: {e}")

try:
    import transformers
    print(f"Transformers: {transformers.__version__}")
except ImportError as e:
    print(f"Transformers Error: {e}")
