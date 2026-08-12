import io
import os

from flask import (
    Flask,
    render_template,
    request,
    flash,
    redirect,
    url_for,
    send_file
)

from crypto_utils import (
    encrypt_message,
    decrypt_message,
    verify_integrity
)

from steganography import (
    hide_data_bytes,
    extract_data_bytes
)

from steganalysis import (
    analyze_image_bytes
)


# ==========================================================
# FLASK CONFIGURATION
# ==========================================================

app = Flask(__name__)

app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "development-secret-key"
)

ALLOWED_EXTENSIONS = {"png"}


# ==========================================================
# FILE VALIDATION
# ==========================================================

def allowed_file(filename):

    return (
        "." in filename
        and
        filename.rsplit(
            ".",
            1
        )[1].lower()
        in ALLOWED_EXTENSIONS
    )


# ==========================================================
# HOME
# ==========================================================

@app.route("/")
def index():

    return render_template(
        "index.html"
    )


# ==========================================================
# ENCRYPT + HIDE
# ==========================================================

@app.route(
    "/hide",
    methods=["POST"]
)
def hide():

    if "image" not in request.files:

        flash(
            "Please select a PNG image."
        )

        return redirect(
            url_for("index")
        )


    image = request.files["image"]

    message = request.form.get(
        "message",
        ""
    ).strip()

    password = request.form.get(
        "password",
        ""
    )


    # Validate image

    if image.filename == "":

        flash(
            "Please select an image."
        )

        return redirect(
            url_for("index")
        )


    if not allowed_file(
        image.filename
    ):

        flash(
            "Only PNG images are supported."
        )

        return redirect(
            url_for("index")
        )


    # Validate message

    if not message:

        flash(
            "Please enter a secret message."
        )

        return redirect(
            url_for("index")
        )


    # Validate password

    if not password:

        flash(
            "Please enter a password."
        )

        return redirect(
            url_for("index")
        )


    try:

        # ------------------------------------------
        # Read image into memory
        # ------------------------------------------

        image_bytes = image.read()


        if not image_bytes:

            raise ValueError(
                "The uploaded image is empty."
            )


        # ------------------------------------------
        # Encrypt message
        # ------------------------------------------

        (
            salt,
            encrypted_message,
            message_hash
        ) = encrypt_message(
            message,
            password
        )


        # ------------------------------------------
        # Convert SHA-256 hash to bytes
        # ------------------------------------------

        hash_bytes = message_hash.encode()


        hash_length = len(
            hash_bytes
        )


        # ------------------------------------------
        # Create hidden payload
        #
        # 16 bytes  → salt
        # 4 bytes   → hash length
        # 64 bytes  → SHA-256 hash
        # remaining → encrypted message
        # ------------------------------------------

        payload = (
            salt
            + hash_length.to_bytes(
                4,
                "big"
            )
            + hash_bytes
            + encrypted_message
        )


        # ------------------------------------------
        # Hide encrypted payload in image
        # ------------------------------------------

        stego_bytes = hide_data_bytes(
            image_bytes,
            payload
        )


        # ------------------------------------------
        # Return stego image
        # ------------------------------------------

        return send_file(
            io.BytesIO(stego_bytes),
            mimetype="image/png",
            as_attachment=True,
            download_name="stego_image.png"
        )


    except ValueError as error:

        flash(
            str(error)
        )

        return redirect(
            url_for("index")
        )


    except Exception as error:

        print(
            "Hide error:",
            error
        )

        flash(
            "Error while encrypting and hiding data."
        )

        return redirect(
            url_for("index")
        )


# ==========================================================
# EXTRACT + DECRYPT
# ==========================================================

@app.route(
    "/extract",
    methods=["POST"]
)
def extract():

    if "stego_image" not in request.files:

        flash(
            "Please select a stego PNG."
        )

        return redirect(
            url_for("index")
        )


    image = request.files[
        "stego_image"
    ]

    password = request.form.get(
        "extract_password",
        ""
    )


    # Validate image

    if image.filename == "":

        flash(
            "Please select a stego image."
        )

        return redirect(
            url_for("index")
        )


    if not allowed_file(
        image.filename
    ):

        flash(
            "Only PNG images are supported."
        )

        return redirect(
            url_for("index")
        )


    # Validate password

    if not password:

        flash(
            "Please enter the password."
        )

        return redirect(
            url_for("index")
        )


    try:

        # ------------------------------------------
        # Read image into memory
        # ------------------------------------------

        image_bytes = image.read()


        if not image_bytes:

            raise ValueError(
                "The uploaded image is empty."
            )


        # ------------------------------------------
        # Extract hidden payload
        # ------------------------------------------

        payload = extract_data_bytes(
            image_bytes
        )


        if len(payload) < 20:

            raise ValueError(
                "Invalid hidden payload."
            )


        # ------------------------------------------
        # Extract salt
        # ------------------------------------------

        salt = payload[:16]


        # ------------------------------------------
        # Extract hash length
        # ------------------------------------------

        hash_length = int.from_bytes(
            payload[16:20],
            "big"
        )


        if hash_length <= 0:

            raise ValueError(
                "Invalid integrity data."
            )


        # ------------------------------------------
        # Extract original SHA-256 hash
        # ------------------------------------------

        hash_start = 20

        hash_end = (
            hash_start
            + hash_length
        )


        if len(payload) < hash_end:

            raise ValueError(
                "Invalid hidden payload."
            )


        original_hash = payload[
            hash_start:hash_end
        ].decode()


        # ------------------------------------------
        # Extract encrypted message
        # ------------------------------------------

        encrypted_message = payload[
            hash_end:
        ]


        if not encrypted_message:

            raise ValueError(
                "No encrypted message found."
            )


        # ------------------------------------------
        # Decrypt message
        # ------------------------------------------

        message = decrypt_message(
            encrypted_message,
            password,
            salt
        )


        # ------------------------------------------
        # Verify integrity
        # ------------------------------------------

        integrity_valid = verify_integrity(
            message,
            original_hash
        )


        if not integrity_valid:

            return render_template(
                "result.html",
                success=False,
                message=None,
                integrity=False,
                error=(
                    "Integrity verification failed. "
                    "The hidden data may have been modified."
                )
            )


        # ------------------------------------------
        # Successful extraction
        # ------------------------------------------

        return render_template(
            "result.html",
            success=True,
            message=message,
            integrity=True,
            error=None
        )


    except Exception as error:

        print(
            "Extraction error:",
            error
        )

        return render_template(
            "result.html",
            success=False,
            message=None,
            integrity=False,
            error=(
                "Incorrect password or invalid "
                "stego image."
            )
        )


# ==========================================================
# STEGANALYSIS
# ==========================================================

@app.route(
    "/analyze",
    methods=["POST"]
)
def analyze():

    if "analysis_image" not in request.files:

        flash(
            "Please select an image to analyze."
        )

        return redirect(
            url_for("index")
        )


    image = request.files[
        "analysis_image"
    ]


    # Validate image

    if image.filename == "":

        flash(
            "Please select an image."
        )

        return redirect(
            url_for("index")
        )


    if not allowed_file(
        image.filename
    ):

        flash(
            "Only PNG images are supported."
        )

        return redirect(
            url_for("index")
        )


    try:

        # ------------------------------------------
        # Read image into memory
        # ------------------------------------------

        image_bytes = image.read()


        if not image_bytes:

            raise ValueError(
                "The uploaded image is empty."
            )


        # ------------------------------------------
        # Analyze image
        # ------------------------------------------

        results = analyze_image_bytes(
            image_bytes
        )


        # ------------------------------------------
        # Display analysis result
        # ------------------------------------------

        return render_template(
            "analysis.html",
            results=results
        )


    except Exception as error:

        print(
            "Analysis error:",
            error
        )

        flash(
            "Unable to analyze the image."
        )

        return redirect(
            url_for("index")
        )


# ==========================================================
# LOCAL DEVELOPMENT
# ==========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )