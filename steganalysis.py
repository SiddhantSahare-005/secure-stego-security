from PIL import Image
import numpy as np


def analyze_image(image_path):
    """
    Analyze an image for statistical characteristics
    that may indicate LSB steganography.
    """

    image = Image.open(image_path).convert("RGB")

    image_array = np.array(image)

    height, width, channels = image_array.shape

    # --------------------------------------------------
    # Basic image information
    # --------------------------------------------------

    total_pixels = height * width

    # --------------------------------------------------
    # LSB analysis
    # --------------------------------------------------

    lsb_values = image_array & 1

    total_lsb_bits = lsb_values.size

    ones = np.sum(lsb_values)

    zeros = total_lsb_bits - ones

    lsb_one_ratio = ones / total_lsb_bits

    lsb_zero_ratio = zeros / total_lsb_bits

    # --------------------------------------------------
    # Pixel statistics
    # --------------------------------------------------

    mean_value = float(
        np.mean(image_array)
    )

    standard_deviation = float(
        np.std(image_array)
    )

    unique_values = len(
        np.unique(image_array)
    )

    # --------------------------------------------------
    # Neighboring pixel differences
    # --------------------------------------------------

    horizontal_difference = np.abs(
        image_array[:, 1:, :].astype(int)
        -
        image_array[:, :-1, :].astype(int)
    )

    average_pixel_difference = float(
        np.mean(horizontal_difference)
    )

    # --------------------------------------------------
    # LSB anomaly score
    # --------------------------------------------------

    # A perfectly balanced LSB distribution is
    # not proof of steganography. It is only one
    # statistical indicator.

    balance_difference = abs(
        lsb_one_ratio - 0.5
    )

    if balance_difference < 0.01:

        lsb_score = 90

    elif balance_difference < 0.03:

        lsb_score = 70

    elif balance_difference < 0.06:

        lsb_score = 45

    else:

        lsb_score = 20

    # --------------------------------------------------
    # Pixel variation score
    # --------------------------------------------------

    if average_pixel_difference > 35:

        pixel_score = 80

    elif average_pixel_difference > 20:

        pixel_score = 60

    elif average_pixel_difference > 10:

        pixel_score = 40

    else:

        pixel_score = 20

    # --------------------------------------------------
    # Overall suspicion score
    # --------------------------------------------------

    suspicion_score = int(
        (lsb_score * 0.7)
        +
        (pixel_score * 0.3)
    )

    # --------------------------------------------------
    # Classification
    # --------------------------------------------------

    if suspicion_score >= 70:

        classification = "HIGH"

    elif suspicion_score >= 45:

        classification = "MEDIUM"

    else:

        classification = "LOW"

    return {
        "width": width,
        "height": height,
        "channels": channels,
        "total_pixels": total_pixels,
        "lsb_zero_ratio": round(
            lsb_zero_ratio * 100,
            2
        ),
        "lsb_one_ratio": round(
            lsb_one_ratio * 100,
            2
        ),
        "mean_pixel_value": round(
            mean_value,
            2
        ),
        "pixel_standard_deviation": round(
            standard_deviation,
            2
        ),
        "unique_values": unique_values,
        "average_pixel_difference": round(
            average_pixel_difference,
            2
        ),
        "lsb_score": lsb_score,
        "pixel_score": pixel_score,
        "suspicion_score": suspicion_score,
        "classification": classification
    }