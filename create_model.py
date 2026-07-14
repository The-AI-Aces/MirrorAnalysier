import tensorflow as tf
from tensorflow.keras import layers, models
import os

print("Creating dummy Keras model for Mirror-Analyzer...")

# Build a simple sequential model matching the expected input/output shapes
model = models.Sequential([
    layers.Input(shape=(224, 224, 3)),
    layers.Conv2D(4, (3, 3), activation='relu'),
    layers.GlobalAveragePooling2D(),
    layers.Dense(8, activation='softmax')
])

# Create destination folder
dest_dir = "model"
if not os.path.exists(dest_dir):
    os.makedirs(dest_dir)

# Save as HDF5 format
model_path = os.path.join(dest_dir, "skin_model_v2.h5")
model.save(model_path)

print("Dummy skin model created successfully at:")
print(os.path.abspath(model_path))
