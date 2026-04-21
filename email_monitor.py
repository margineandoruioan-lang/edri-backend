"""
EDRI — Email Monitor
Monitorizare invoice@ddl-intelligentsolutions.com
Fisier NOU — nu modifica nimic existent
"""

import os
import json
import time
import imaplib
import email
import tempfile
from email.header import decode_header
from pathlib import Path
from document_processor import process_document, extract_financial_indicators

# ══ CONFIGURATIE EMAIL ══
EMAIL_CONFIG = {
    'address': 'invoice@ddl-intelligentsolutions.com',
    'imap_server': os.environ.get('IMAP_SERVER', 'imap.hostinger.com'),  # Hostinger
    'imap_port': int(os.environ.get('IMAP_PORT', '993')),
    'password': os.environ.get('EMAIL_PASSWORD', '@8cM8/nhG0hw'),
    'check_interval_seconds': 300,  # verifica la fiecare 5 minute
    'processed_folder': 'EDRI_Processed',
    'error_folder': 'EDRI_Errors'
}

# Extensii acceptate
ACCEPTED_EXTENSIONS = {
    '.xlsx', '.xls', '.pdf', '.docx', '.doc',
    '.html', '.htm', '.csv', '.jpg', '.jpeg', '.png', '.tiff'
}

# Cuvinte cheie care indica documente financiare
FINANCIAL_KEYWORDS = [
    'balanta', 'bilant', 'situatie', 'financiar', 'contabil',
    'raport', 'analiza', 'invoice', 'factura', 'sold', 'cont'
]

def decode_mime_header(header):
    """Decodifica header email (subject, from etc)"""
    decoded = decode_header(header)
    parts = []
    for part, enc in decoded:
        if isinstance(part, bytes):
            parts.append(part.decode(enc or 'utf-8', errors='replace'))
        else:
            parts.append(str(part))
    return ' '.join(parts)

def is_financial_document(filename, subject=''):
    """Verifica daca fisierul este probabil un document financiar"""
    ext = Path(filename).suffix.lower()
    if ext not in ACCEPTED_EXTENSIONS:
        return False
    name_lower = filename.lower() + subject.lower()
    return any(kw in name_lower for kw in FINANCIAL_KEYWORDS) or ext in ('.xlsx', '.xls', '.pdf')

def connect_imap():
    """Conectare la server IMAP Hostinger"""
    try:
        mail = imaplib.IMAP4_SSL(
            EMAIL_CONFIG['imap_server'],
            EMAIL_CONFIG['imap_port']
        )
        mail.login(EMAIL_CONFIG['address'], EMAIL_CONFIG['password'])
        return mail
    except Exception as e:
        print(f"[EDRI Email Monitor] Eroare conectare IMAP: {e}")
        return None

def ensure_folder(mail, folder_name):
    """Creeaza folder IMAP daca nu exista"""
    try:
        result = mail.create(folder_name)
    except:
        pass

def process_email(mail, email_id):
    """Proceseaza un email cu atașamente financiare"""
    try:
        _, data = mail.fetch(email_id, '(RFC822)')
        raw = data[0][1]
        msg = email.message_from_bytes(raw)

        subject = decode_mime_header(msg.get('Subject', ''))
        sender = decode_mime_header(msg.get('From', ''))
        results = []

        for part in msg.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get('Content-Disposition') is None:
                continue

            filename = part.get_filename()
            if not filename:
                continue
            filename = decode_mime_header(filename)

            if not is_financial_document(filename, subject):
                continue

            # Salvam fisierul temporar
            file_data = part.get_payload(decode=True)
            if not file_data:
                continue

            with tempfile.NamedTemporaryFile(
                suffix=Path(filename).suffix,
                delete=False
            ) as tmp:
                tmp.write(file_data)
                tmp_path = tmp.name

            try:
                # METODA 3 — procesare
                raw_result = process_document(tmp_path, filename)
                indicators = extract_financial_indicators(raw_result.get('data', {}))

                result = {
                    'email_subject': subject,
                    'email_from': sender,
                    'filename': filename,
                    'format': raw_result.get('format'),
                    'method_used': raw_result.get('method'),
                    'status': raw_result.get('status'),
                    'indicators': indicators
                }
                results.append(result)
                print(f"[EDRI] ✓ Procesat: {filename} | Metodă: {raw_result.get('method')} | Indicatori: {len(indicators)}")

            except Exception as e:
                print(f"[EDRI] Eroare procesare {filename}: {e}")
            finally:
                try:
                    os.unlink(tmp_path)
                except:
                    pass

        return results

    except Exception as e:
        print(f"[EDRI Email Monitor] Eroare procesare email: {e}")
        return []

def check_inbox():
    """
    Verifica inbox-ul pentru emailuri noi cu documente financiare
    Apelata la fiecare check_interval_seconds
    """
    if not EMAIL_CONFIG['password']:
        print("[EDRI Email Monitor] EMAIL_PASSWORD nu este setat in environment variables")
        return []

    mail = connect_imap()
    if not mail:
        return []

    all_results = []
    try:
        mail.select('INBOX')
        ensure_folder(mail, EMAIL_CONFIG['processed_folder'])

        # Cauta emailuri nevazute
        _, ids = mail.search(None, 'UNSEEN')
        email_ids = ids[0].split() if ids[0] else []

        if email_ids:
            print(f"[EDRI Email Monitor] {len(email_ids)} emailuri noi detectate")

        for email_id in email_ids:
            results = process_email(mail, email_id)
            if results:
                all_results.extend(results)
                # Muta in folderul Processed
                try:
                    mail.copy(email_id, EMAIL_CONFIG['processed_folder'])
                    mail.store(email_id, '+FLAGS', '\\Deleted')
                except:
                    pass

        mail.expunge()

    except Exception as e:
        print(f"[EDRI Email Monitor] Eroare inbox: {e}")
    finally:
        try:
            mail.logout()
        except:
            pass

    return all_results

def run_monitor():
    """Porneste monitorizarea continua a emailului"""
    print(f"[EDRI Email Monitor] Pornit · {EMAIL_CONFIG['address']} · interval: {EMAIL_CONFIG['check_interval_seconds']}s")
    while True:
        try:
            results = check_inbox()
            if results:
                print(f"[EDRI] {len(results)} documente procesate")
        except Exception as e:
            print(f"[EDRI Email Monitor] Eroare: {e}")
        time.sleep(EMAIL_CONFIG['check_interval_seconds'])

if __name__ == '__main__':
    run_monitor()
