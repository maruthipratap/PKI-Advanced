from flask import Blueprint, jsonify, render_template, request, Response
from app.revocation.crl_manager import generate_crl, get_crl_info
from app.revocation.ocsp import build_ocsp_response

crl_ocsp_bp = Blueprint('crl_ocsp', __name__)


@crl_ocsp_bp.route('/crl')
def view_crl():
    """Generate and display the current CRL."""
    crl_info = get_crl_info()
    crl_pem  = generate_crl()
    return render_template('crl.html', crl_info=crl_info, crl_pem=crl_pem)


@crl_ocsp_bp.route('/crl/download')
def download_crl():
    """Download the CRL as a .pem file."""
    crl_pem = generate_crl()
    return Response(
        crl_pem,
        mimetype='application/x-pem-file',
        headers={"Content-Disposition": "attachment; filename=crl.pem"}
    )


@crl_ocsp_bp.route('/ocsp/<serial_number>')
def ocsp_check(serial_number):
    """OCSP-style JSON endpoint. Query: /ocsp/<serial_number>"""
    response = build_ocsp_response(serial_number)
    return jsonify(response)


@crl_ocsp_bp.route('/ocsp', methods=['GET', 'POST'])
def ocsp_ui():
    """Web UI for OCSP checking."""
    result = None
    if request.method == 'POST':
        serial = request.form.get('serial', '').strip()
        if serial:
            result = build_ocsp_response(serial)
    return render_template('ocsp.html', result=result)