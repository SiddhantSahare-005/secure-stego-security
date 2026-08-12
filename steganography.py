from io import BytesIO

from PIL import Image


DELIMITER = "1111111111111110"


def bytes_to_bits(data):
    """Convert bytes into binary bits."""

    return "".join(
        format(byte, "08b")
        for byte in data
    )


def bits_to_bytes(bits):
    """Convert binary bits back into bytes."""

    if len(bits) % 8 != 0:
        raise ValueError(
            "Invalid hidden data."
        )

    return bytes(
        int(bits[i:i + 8], 2)
        for i in range(0, len(bits), 8)
    )


# ==========================================================
# HIDE DATA
# ==========================================================

def hide_data(image_path, data, output_path):
    """
    Existing local file-based hiding function.

    Keeps your current local application working.
    """

    image = Image.open(
        image_path
    ).convert("RGB")

    stego_image = _embed_data(
        image,
        data
    )

    stego_image.save(
        output_path,
        format="PNG"
    )

    return output_path


def hide_data_bytes(image_bytes, data):
    """
    Hide data inside an image supplied as bytes.

    Used by Vercel.
    Returns the generated PNG as bytes.
    """

    image = Image.open(
        BytesIO(image_bytes)
    ).convert("RGB")

    stego_image = _embed_data(
        image,
        data
    )

    output = BytesIO()

    stego_image.save(
        output,
        format="PNG"
    )

    output.seek(0)

    return output.getvalue()


def _embed_data(image, data):
    """
    Internal function that performs LSB embedding.
    """

    pixels = list(
        image.getdata()
    )

    data_bits = bytes_to_bits(
        data
    )

    payload = (
        data_bits
        + DELIMITER
    )

    max_capacity = (
        len(pixels) * 3
    )

    if len(payload) > max_capacity:

        raise ValueError(
            "Data is too large for this image."
        )

    new_pixels = []

    bit_index = 0

    for pixel in pixels:

        new_pixel = list(pixel)

        for channel in range(3):

            if bit_index < len(payload):

                bit = int(
                    payload[bit_index]
                )

                new_pixel[channel] = (
                    new_pixel[channel] & 254
                ) | bit

                bit_index += 1

        new_pixels.append(
            tuple(new_pixel)
        )

    stego_image = Image.new(
        "RGB",
        image.size
    )

    stego_image.putdata(
        new_pixels
    )

    return stego_image


# ==========================================================
# EXTRACT DATA
# ==========================================================

def extract_data(image_path):
    """
    Existing local file-based extraction function.
    """

    with open(
        image_path,
        "rb"
    ) as file:

        image_bytes = file.read()

    return extract_data_bytes(
        image_bytes
    )


def extract_data_bytes(image_bytes):
    """
    Extract hidden data from image bytes.

    Used by Vercel.
    """

    image = Image.open(
        BytesIO(image_bytes)
    ).convert("RGB")

    pixels = list(
        image.getdata()
    )

    bits = ""

    for pixel in pixels:

        for channel in pixel:

            bits += str(
                channel & 1
            )

    delimiter_position = bits.find(
        DELIMITER
    )

    if delimiter_position == -1:

        raise ValueError(
            "No hidden data found."
        )

    data_bits = bits[
        :delimiter_position
    ]

    if not data_bits:

        raise ValueError(
            "Hidden data is empty."
        )

    return bits_to_bytes(
        data_bits
    )