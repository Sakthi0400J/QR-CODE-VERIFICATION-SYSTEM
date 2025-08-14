from flask import Flask, render_template, request, redirect, url_for, flash
from urllib.parse import urlencode
import io
import csv
from PIL import Image
import qrcode
import base64

app = Flask(__name__)
app.secret_key = '1234' 


def generate_qr_code(data, size=200):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    
    if size:
        img = img.resize((size, size), Image.LANCZOS)

   
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

def add_qr_to_certificate(certificate_image, qr_data, qr_size=200, padding=250):
    
    certificate = Image.open(certificate_image).convert("RGBA")
    qr_code_stream = generate_qr_code(qr_data, size=qr_size)
    qr_code = Image.open(qr_code_stream).convert("RGBA")

    position = (
        certificate.width - qr_code.width - 350,
        certificate.height - qr_code.height - padding
    )

    certificate.paste(qr_code, position, qr_code)


    output_stream = io.BytesIO()
    certificate = certificate.convert("RGB")
    certificate.save(output_stream, format='JPEG', quality=95)
    output_stream.seek(0)
    return output_stream

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        id = request.form['id']
        name = request.form['name']
        course = request.form['course']
        college = request.form['college']
        date = request.form['date']

        if 'certificate' not in request.files:
            flash('No file part')
            return redirect(request.url)

        file = request.files['certificate']

        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        certificate_image = io.BytesIO(file.read())
        qr_data = "http://localhost:5000/verify?" + urlencode({"user_id": id}) 
        output_stream = add_qr_to_certificate(certificate_image, qr_data)

        img_base64 = base64.b64encode(output_stream.getvalue()).decode('utf-8')
        img_data = f"data:image/jpeg;base64,{img_base64}"

        with open('data/user_data.csv', mode='a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([id, name, course, college, date])

        flash('Data submitted successfully! Certificate generated with QR code.')
        return render_template('display_certificate.html', img_data=img_data, filename=f"certificate_with_qr_{id}.jpg")

    return render_template('index.html')

@app.route('/verify')
def show_user():
    user_id = request.args.get('user_id')
    print(f"User ID received for verification: {user_id}")

    if not user_id:
        return "User ID is required", 400

    user_data = None
    try:
        with open('data/user_data.csv', 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                if row[0] == user_id: 
                    user_data = {
                        'id': row[0],
                        'name': row[1],
                        'course': row[2],
                        'college': row[3],
                        'date': row[4]
                    }
                    break
    except FileNotFoundError:
        return "User data file not found.", 500


    return render_template('user.html', user=user_data)


if __name__ == '__main__':
    app.run(debug=True)
