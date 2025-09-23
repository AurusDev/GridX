from PIL import Image

def gerar_ico(arquivo_png, saida_ico="gridx.ico"):
    """
    Gera um arquivo .ico com múltiplos tamanhos a partir de um .png
    """
    try:
        img = Image.open(arquivo_png)

        # salva como .ico com múltiplas resoluções
        img.save(saida_ico, format="ICO", sizes=[
            (16, 16), (32, 32), (48, 48),
            (64, 64), (128, 128), (256, 256)
        ])
        print(f"✅ Ícone gerado com sucesso: {saida_ico}")

    except Exception as e:
        print(f"❌ Erro ao gerar ícone: {e}")


if __name__ == "__main__":
    # Troque aqui pelo nome do seu arquivo PNG
    gerar_ico(r"C:\Users\User\Documents\python_projects\python_projects\gridx_1.png")
