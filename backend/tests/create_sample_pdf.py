"""
Helper script to generate a valid sample legal PDF for testing.
"""
from pathlib import Path


def create_sample_pdf():
    sample_dir = Path(__file__).parent / "sample_data"
    sample_dir.mkdir(parents=True, exist_ok=True)

    pdf_path = sample_dir / "sample_fir.pdf"

    pdf_bytes = (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>\nendobj\n"
        b"4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
        b"5 0 obj\n<< /Length 120 >>\nstream\n"
        b"BT\n/F1 12 Tf\n100 700 Td\n(FIRST INFORMATION REPORT - FIR 102/2026) Tj\n0 -20 Td\n(Police Station Central Delhi. Offense: Section 303 of BNS.) Tj\nET\n"
        b"endstream\nendobj\n"
        b"xref\n0 6\n0000000000 65535 f\n0000000009 00000 n\n0000000062 00000 n\n0000000125 00000 n\n0000000250 00000 n\n0000000319 00000 n\n"
        b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n490\n%%EOF\n"
    )

    pdf_path.write_bytes(pdf_bytes)
    print(f"Valid sample PDF written to {pdf_path}")


if __name__ == "__main__":
    create_sample_pdf()
