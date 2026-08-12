import os
import uuid

from flask import (
    Flask,
    render_template,
    request,
    flash,
    redirect,
    url_for,
    send_file
)

from werkzeug.utils import secure_filename

from crypto_utils import (
    encrypt_message,
    decrypt_message,
    verify_integrity
)

from steganography import (
    hide_data,
    extract_data
)

from steganalysis import (
    analyze_image
)


app = Flask(__name__)

app.secret_key = "stego-security-secret-key"


UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "output"

ALLOWED_EXTENSIONS = {"png"}


app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER


os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)

os.makedirs(
    OUTPUT_FOLDER,
    exist_ok=True
)


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


    if not message:

        flash(
            "Please enter a secret message."
        )

        return redirect(
            url_for("index")
        )


    if not password:

        flash(
            "Please enter a password."
        )

        return redirect(
            url_for("index")
        )


    unique_id = uuid.uuid4().hex

    filename = secure_filename(
        image.filename
    )


    input_path = os.path.join(
        UPLOAD_FOLDER,
        f"{unique_id}_{filename}"
    )


    output_path = os.path.join(
        OUTPUT_FOLDER,
        f"stego_{unique_id}.png"
    )


    image.save(
        input_path
    )


    try:

        # Encrypt message

        (
            salt,
            encrypted_message,
            message_hash
        ) = encrypt_message(
            message,
            password
        )


        # Convert SHA-256 hash to bytes

        hash_bytes = message_hash.encode()


        # Store hash length

        hash_length = len(
            hash_bytes
        )


        # Payload structure:
        #
        # 16 bytes  -> salt
        # 4 bytes   -> hash length
        # 64 bytes  -> SHA-256 hash
        # remaining -> encrypted message

        payload = (
            salt
            + hash_length.to_bytes(
                4,
                "big"
            )
            + hash_bytes
            + encrypted_message
        )


        # Hide encrypted payload

        hide_data(
            input_path,
            payload,
            output_path
        )


    except ValueError as error:

        flash(
            str(error)
        )

        return redirect(
            url_for("index")
        )


    except Exception as error:

        print(error)

        flash(
            "Error while encrypting and hiding data."
        )

        return redirect(
            url_for("index")
        )


    return render_template(
        "success.html",
        filename=os.path.basename(
            output_path
        )
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


    if not password:

        flash(
            "Please enter the password."
        )

        return redirect(
            url_for("index")
        )


    unique_id = uuid.uuid4().hex

    filename = secure_filename(
        image.filename
    )


    input_path = os.path.join(
        UPLOAD_FOLDER,
        f"extract_{unique_id}_{filename}"
    )


    image.save(
        input_path
    )


    try:

        # Extract hidden payload

        payload = extract_data(
            input_path
        )


        # -------------------------------
        # Extract salt
        # -------------------------------

        if len(payload) < 20:

            raise ValueError(
                "Invalid hidden payload."
            )


        salt = payload[:16]


        # -------------------------------
        # Extract hash length
        # -------------------------------

        hash_length = int.from_bytes(
            payload[16:20],
            "big"
        )


        # -------------------------------
        # Extract original hash
        # -------------------------------

        hash_start = 20

        hash_end = (
            hash_start
            + hash_length
        )


        original_hash = payload[
            hash_start:hash_end
        ].decode()


        # -------------------------------
        # Extract encrypted message
        # -------------------------------

        encrypted_message = payload[
            hash_end:
        ]


        if not encrypted_message:

            raise ValueError(
                "No encrypted message found."
            )


        # -------------------------------
        # Decrypt
        # -------------------------------

        message = decrypt_message(
            encrypted_message,
            password,
            salt
        )


        # -------------------------------
        # Verify integrity
        # -------------------------------

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
                error="Integrity verification failed."
            )


        return render_template(
            "result.html",
            success=True,
            message=message,
            integrity=True,
            error=None
        )


    except Exception as error:

        print(error)

        return render_template(
            "result.html",
            success=False,
            message=None,
            integrity=False,
            error=(
                "Incorrect password or "
                "invalid stego image."
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


    unique_id = uuid.uuid4().hex

    filename = secure_filename(
        image.filename
    )


    input_path = os.path.join(
        UPLOAD_FOLDER,
        f"analysis_{unique_id}_{filename}"
    )


    image.save(
        input_path
    )


    try:

        results = analyze_image(
            input_path
        )


        return render_template(
            "analysis.html",
            results=results
        )


    except Exception as error:

        print(error)

        flash(
            "Unable to analyze the image."
        )

        return redirect(
            url_for("index")
        )


# ==========================================================
# DOWNLOAD
# ==========================================================

@app.route(
    "/download/<filename>"
)
def download(filename):

    safe_filename = secure_filename(
        filename
    )


    file_path = os.path.join(
        OUTPUT_FOLDER,
        safe_filename
    )


    if not os.path.exists(
        file_path
    ):

        flash(
            "File not found."
        )

        return redirect(
            url_for("index")
        )


    return send_file(
        file_path,
        as_attachment=True
    )


# ==========================================================
# RUN
# ==========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )