import feedparser
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime
import os
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive


# =========================
# 1. Buscar notícias via RSS
# =========================
def get_news():
    url = "https://g1.globo.com/dynamo/rss2.xml"  # Feed RSS do G1
    feed = feedparser.parse(url)

    articles = []
    for entry in feed.entries[:5]:  # pega as 5 primeiras
        articles.append({
            "title": entry.title,
            "description": entry.summary,
            "url": entry.link
        })
    return articles


# =========================
# 2. Criar PDF com as notícias
# =========================
def create_pdf(news_data, filename="noticias.pdf"):
    if not news_data:
        print("⚠️ Nenhuma notícia disponível. PDF não foi gerado.")
        return None

    # Gera nome único para evitar conflito
    filename = f"noticias_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    styles = getSampleStyleSheet()
    story = []
    
    # Cabeçalho
    story.append(Paragraph("Relatório de Notícias", styles['Title']))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Data de geração: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
    story.append(Spacer(1, 24))
    
    # Inserir notícias
    for i, article in enumerate(news_data, 1):
        story.append(Paragraph(f"<b>{i}. {article['title']}</b>", styles['Heading3']))
        story.append(Paragraph(article['description'], styles['Normal']))
        story.append(Paragraph(f"<a href='{article['url']}'>Leia mais</a>", styles['Normal']))
        story.append(Spacer(1, 12))
    
    # Criar PDF
    doc = SimpleDocTemplate(filename, pagesize=A4)
    doc.build(story)
    print(f"✅ PDF gerado: {filename}")
    return filename


# =========================
# 3. Upload para Google Drive
# =========================
def drive_login():
    gauth = GoogleAuth()

    # Caminho absoluto do client_secrets.json (mesma pasta do script)
    secrets_path = os.path.join(os.path.dirname(__file__), "client_secrets.json")
    gauth.LoadClientConfigFile(secrets_path)

    if not gauth.credentials:
        gauth.LocalWebserverAuth()  # abre navegador p/ login
    elif gauth.access_token_expired:
        gauth.Refresh()
    else:
        gauth.Authorize()

    # Salva credenciais para não pedir login toda vez
    gauth.SaveCredentialsFile("credentials.json")
    return GoogleDrive(gauth)


def upload_to_drive(filename, folder_id):
    drive = drive_login()
    file_drive = drive.CreateFile({
        "title": os.path.basename(filename),
        "parents": [{"id": folder_id}]
    })
    file_drive.SetContentFile(filename)
    file_drive.Upload()
    print(f"✅ Upload concluído: {filename} -> Google Drive")


# =========================
# Execução principal
# =========================
if __name__ == "__main__":
    noticias = get_news()

    # Debug no terminal
    for i, art in enumerate(noticias, 1):
        print(f"\n{i}. {art['title']}")
        print(art['description'])

    # Gerar PDF
    pdf_file = create_pdf(noticias)

    # Fazer upload (pasta fornecida)
    if pdf_file:
        folder_id = "1gH0vSs5pQIfMX4uocVrDYxXCWunHP71Y"
        upload_to_drive(pdf_file, folder_id)
