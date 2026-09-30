import tensorflow as tf
import numpy as np
import matplotlib.pyplot as plt
from tensorflow.keras.utils import load_img, img_to_array

# Load model
model = tf.keras.models.load_model("old.keras")

# IMPORTANT:
# Use the exact order printed by train_ds.class_names
class_names =['battery', 'biological', 'cardboard', 'clothes', 'glass', 'metal', 'paper', 'plastic', 'shoes', 'trash']

# Image
image_path = "Plastic_4.jpg"

img = load_img(
    image_path,
    target_size=(256, 256)
)

img_array = img_to_array(img)

# Add batch dimension
img_array = np.expand_dims(img_array, axis=0)

# DON'T divide by 255 here if your model
# already contains layers.Rescaling(1./255)

prediction = model.predict(img_array)

# Get probabilities
probabilities = prediction[0]

# Get predicted class
predicted_index = np.argmax(probabilities)

predicted_class = class_names[predicted_index]

confidence = probabilities[predicted_index] * 100

print("\nPredicted:", predicted_class)
print("Confidence:", round(confidence, 2), "%")

# Show all predictions
print("\nAll predictions:")

for i in range(len(class_names)):
    print(
        f"{class_names[i]}: "
        f"{probabilities[i] * 100:.2f}%"
    )

# Display image
plt.imshow(img)
plt.axis("off")
plt.title(
    f"{predicted_class} ({confidence:.2f}%)"
)
plt.show()